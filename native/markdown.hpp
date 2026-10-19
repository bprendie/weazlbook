#pragma once
#include <string>
#include <vector>
namespace wb {
class Markdown {
 std::string path_;
 std::vector<long> boundaries_;
public:
 explicit Markdown(const std::string& path);
 size_t chapters() const {return boundaries_.size()-1;}
 std::string chapter(size_t index) const;
};
bool markdown_extension(const std::string& path);
std::string markdown_text(const std::string& input);
std::string markdown_file(const std::string& path);
}
