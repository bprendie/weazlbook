#pragma once
#include <string>
#include <vector>
#include <cstdint>
namespace wb {
struct Chapter {std::string path,title;};
struct Epub {
 std::string file,title;
 std::vector<Chapter> spine;
 explicit Epub(const std::string&path);
 std::string chapter(size_t index)const;
};
}
