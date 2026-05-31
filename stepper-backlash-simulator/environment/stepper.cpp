#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

struct Row {
    int tick;
    int target;
};

struct Counters {
    int idle = 0;
    int slewing = 0;
    int backlash = 0;
    int aborted = 0;
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

static int parse_config_int(const std::string& path, const std::string& key) {
    std::ifstream handle(path);
    if (!handle.is_open()) {
        throw std::runtime_error("failed to open config");
    }
    std::string line;
    while (std::getline(handle, line)) {
        const std::size_t pos = line.find(key);
        if (pos == std::string::npos) {
            continue;
        }
        const std::size_t colon = line.find(':', pos);
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
    throw std::runtime_error(key + " not found");
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
        if (parts.size() != 2) {
            throw std::runtime_error("unexpected tsv shape");
        }
        rows.push_back(Row{std::stoi(parts[0]), std::stoi(parts[1])});
    }
    return rows;
}

int main(int argc, char* argv[]) {
    if (argc != 4) {
        return 1;
    }

    const std::string input_dir = argv[1];
    const std::string timeline_path = argv[2];
    const std::string report_path = argv[3];

    const int slew_ticks = parse_config_int(input_dir + "/config.json", "slew_ticks");
    const int backlash_ticks = parse_config_int(input_dir + "/config.json", "backlash_ticks");
    const std::vector<Row> command_rows = load_rows(input_dir + "/commands.tsv");

    std::ofstream timeline(timeline_path);
    timeline << "tick\tposition\tstate\n";

    Counters counters;
    int position = 0;
    std::string state = "IDLE";
    
    // TODO: Track mechanical direction, backlash, and slewing to generate correct exact outputs.
    for (std::size_t index = 0; index < command_rows.size(); ++index) {
        const Row& cmd = command_rows[index];
        
        if (index == 0) {
            position = cmd.target;
        }

        timeline << cmd.tick << '\t' << position << '\t' << state << '\n';
        counters.idle++;
    }

    std::ofstream report(report_path);
    report << "{\n";
    report << "  \"idle_ticks\": " << counters.idle << ",\n";
    report << "  \"slewing_ticks\": " << counters.slewing << ",\n";
    report << "  \"backlash_ticks\": " << counters.backlash << ",\n";
    report << "  \"aborted_backlash_events\": " << counters.aborted << "\n";
    report << "}\n";
    return 0;
}
