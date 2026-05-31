#!/bin/sh
set -eu
cat > /environment/inverter.cpp <<'EOF'
#include <fstream>
#include <iostream>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

struct Row {
    int tick;
    std::string a;
    std::string b;
    std::string c;
};

struct PhaseState {
    std::string requested;
    std::string committed;
    std::string armed;
    bool has_pending = false;
    int dead_ticks_remaining = 0;
    char holding_rail = '?';
    char last_realized_node = 'Z';
};

struct Counters {
    int tu = 0;
    int tl = 0;
    int du = 0;
    int dl = 0;
    int off = 0;
    int restarts = 0;
};

static std::vector<std::string> split_tab_line(const std::string& line) {
    std::vector<std::string> parts;
    std::stringstream stream(line);
    std::string part;
    while (std::getline(stream, part, '\t')) {
        parts.push_back(part);
    }
    return parts;
}

static int parse_dead_time_ticks(const std::string& path) {
    std::ifstream handle(path);
    if (!handle.is_open()) {
        throw std::runtime_error("failed to open config");
    }
    std::string line;
    while (std::getline(handle, line)) {
        const std::size_t key = line.find("dead_time_ticks");
        if (key == std::string::npos) {
            continue;
        }
        const std::size_t colon = line.find(':', key);
        if (colon == std::string::npos) {
            continue;
        }
        std::string digits;
        for (std::size_t i = colon + 1; i < line.size(); ++i) {
            if (line[i] >= '0' && line[i] <= '9') {
                digits.push_back(line[i]);
            } else if (!digits.empty()) {
                break;
            }
        }
        if (!digits.empty()) {
            return std::stoi(digits);
        }
    }
    throw std::runtime_error("dead_time_ticks not found");
}

static std::vector<Row> load_rows(const std::string& path) {
    std::ifstream handle(path);
    if (!handle.is_open()) {
        throw std::runtime_error("failed to open tsv");
    }
    std::string line;
    std::getline(handle, line);
    std::vector<Row> rows;
    while (std::getline(handle, line)) {
        if (line.empty()) {
            continue;
        }
        const std::vector<std::string> parts = split_tab_line(line);
        if (parts.size() != 4) {
            throw std::runtime_error("unexpected tsv shape");
        }
        rows.push_back(Row{std::stoi(parts[0]), parts[1], parts[2], parts[3]});
    }
    return rows;
}

static char rail_from_command(const std::string& command) {
    return command == "U" ? 'P' : 'N';
}

static std::pair<std::string, char> realized_from_dead_time(const std::string& sign) {
    if (sign == "+") {
        return {"DL", 'N'};
    }
    if (sign == "-") {
        return {"DU", 'P'};
    }
    return {"OFF", 'Z'};
}

static std::pair<std::string, char> realized_from_committed(const std::string& command) {
    if (command == "U") {
        return {"TU", 'P'};
    }
    return {"TL", 'N'};
}

static bool sign_sustains_rail(const std::string& sign, char rail) {
    return (sign == "+" && rail == 'N') || (sign == "-" && rail == 'P');
}

static std::pair<std::string, char> realized_from_holding_rail(char rail) {
    if (rail == 'P') {
        return {"DU", 'P'};
    }
    return {"DL", 'N'};
}

static int node_level(char node) {
    if (node == 'P') {
        return 1;
    }
    if (node == 'N') {
        return -1;
    }
    return 0;
}

static std::string compare_nodes(char left, char right) {
    const int l = node_level(left);
    const int r = node_level(right);
    if (l > r) {
        return "+";
    }
    if (l < r) {
        return "-";
    }
    return "0";
}

static void bump_counter(Counters& counters, const std::string& mode) {
    if (mode == "TU") {
        ++counters.tu;
    } else if (mode == "TL") {
        ++counters.tl;
    } else if (mode == "DU") {
        ++counters.du;
    } else if (mode == "DL") {
        ++counters.dl;
    } else {
        ++counters.off;
    }
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        return 1;
    }

    const std::string input_dir = argv[1];
    const std::string timeline_path = argv[2];
    const std::string report_path = argv[3];

    const int dead_time_ticks = parse_dead_time_ticks(input_dir + "/config.json");
    const std::vector<Row> command_rows = load_rows(input_dir + "/commands.tsv");
    const std::vector<Row> current_rows = load_rows(input_dir + "/currents.tsv");
    if (command_rows.size() != current_rows.size()) {
        throw std::runtime_error("row count mismatch");
    }

    std::map<char, PhaseState> states;
    std::map<char, Counters> counters;
    for (char phase : std::string("ABC")) {
        states[phase] = PhaseState{};
        counters[phase] = Counters{};
    }

    std::ofstream timeline(timeline_path);
    timeline << "tick\tA_mode\tA_node\tB_mode\tB_node\tC_mode\tC_node\tVab\tVbc\tVca\n";

    for (std::size_t index = 0; index < command_rows.size(); ++index) {
        const Row& cmd = command_rows[index];
        const Row& cur = current_rows[index];
        if (cmd.tick != cur.tick) {
            throw std::runtime_error("tick mismatch");
        }

        std::map<char, std::string> commands{{'A', cmd.a}, {'B', cmd.b}, {'C', cmd.c}};
        std::map<char, std::string> signs{{'A', cur.a}, {'B', cur.b}, {'C', cur.c}};
        std::map<char, std::pair<std::string, char>> realized;

        for (char phase : std::string("ABC")) {
            PhaseState& state = states[phase];
            const std::string& command = commands[phase];
            const std::string& sign = signs[phase];

            if (index == 0) {
                state.requested = command;
                state.committed = command;
                state.last_realized_node = rail_from_command(command);
            } else if (command != state.requested) {
                const bool restarting_dead_time = state.dead_ticks_remaining > 0;
                if (!state.has_pending) {
                    state.holding_rail = state.last_realized_node == 'Z' ? rail_from_command(state.committed) : state.last_realized_node;
                }
                state.requested = command;
                state.armed = command;
                state.has_pending = true;
                if (restarting_dead_time) {
                    ++counters[phase].restarts;
                }
                state.dead_ticks_remaining = dead_time_ticks;
            }

            std::pair<std::string, char> output;
            if (state.has_pending && state.dead_ticks_remaining > 0) {
                output = realized_from_dead_time(sign);
            } else if (state.has_pending) {
                if (sign_sustains_rail(sign, state.holding_rail)) {
                    output = realized_from_holding_rail(state.holding_rail);
                } else {
                    state.committed = state.armed;
                    state.has_pending = false;
                    output = realized_from_committed(state.committed);
                }
            } else {
                output = realized_from_committed(state.committed);
            }

            realized[phase] = output;
            state.last_realized_node = output.second;
            bump_counter(counters[phase], output.first);
        }

        timeline << cmd.tick << '\t'
                 << realized['A'].first << '\t' << realized['A'].second << '\t'
                 << realized['B'].first << '\t' << realized['B'].second << '\t'
                 << realized['C'].first << '\t' << realized['C'].second << '\t'
                 << compare_nodes(realized['A'].second, realized['B'].second) << '\t'
                 << compare_nodes(realized['B'].second, realized['C'].second) << '\t'
                 << compare_nodes(realized['C'].second, realized['A'].second) << '\n';

        for (char phase : std::string("ABC")) {
            if (states[phase].dead_ticks_remaining > 0) {
                --states[phase].dead_ticks_remaining;
            }
        }
    }

    std::ofstream report(report_path);
    report << "{\n";
    report << "  \"upper_transistor_ticks\": {\"A\": " << counters['A'].tu << ", \"B\": " << counters['B'].tu << ", \"C\": " << counters['C'].tu << "},\n";
    report << "  \"lower_transistor_ticks\": {\"A\": " << counters['A'].tl << ", \"B\": " << counters['B'].tl << ", \"C\": " << counters['C'].tl << "},\n";
    report << "  \"upper_diode_ticks\": {\"A\": " << counters['A'].du << ", \"B\": " << counters['B'].du << ", \"C\": " << counters['C'].du << "},\n";
    report << "  \"lower_diode_ticks\": {\"A\": " << counters['A'].dl << ", \"B\": " << counters['B'].dl << ", \"C\": " << counters['C'].dl << "},\n";
    report << "  \"floating_ticks\": {\"A\": " << counters['A'].off << ", \"B\": " << counters['B'].off << ", \"C\": " << counters['C'].off << "},\n";
    report << "  \"restarted_deadtime_events\": {\"A\": " << counters['A'].restarts << ", \"B\": " << counters['B'].restarts << ", \"C\": " << counters['C'].restarts << "}\n";
    report << "}\n";
    return 0;
}

EOF

g++ -std=c++17 -O2 -Wall -Wextra -o /tmp/inverter /environment/inverter.cpp
/tmp/inverter /environment/sample_job /tmp/inverter_timeline.tsv /tmp/inverter_report.json
