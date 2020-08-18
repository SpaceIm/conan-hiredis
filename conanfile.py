import os

from conans import ConanFile, CMake, tools

class HiredisConan(ConanFile):
    name = "hiredis"
    description = "Hiredis is a minimalistic C client library for the Redis database."
    license = "BSD-3-Clause"
    topics = ("conan", "hiredis", "redis", "client", "database")
    homepage = "https://github.com/redis/hiredis"
    url = "https://github.com/conan-io/conan-center-index"
    exports_sources = "CMakeLists.txt"
    generators = "cmake", "cmake_find_package"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "with_ssl": [True, False]
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "with_ssl": False
    }

    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.libcxx
        del self.settings.compiler.cppstd

    def requirements(self):
        if self.options.with_ssl:
            self.requires("openssl/1.1.1g")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(self.name + "-" + self.version, self._source_subfolder)

    def build(self):
        tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                              "ADD_LIBRARY(hiredis SHARED ${hiredis_sources})",
                              "ADD_LIBRARY(hiredis ${hiredis_sources})")
        tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                              "ADD_LIBRARY(hiredis_ssl SHARED",
                              "ADD_LIBRARY(hiredis_ssl")
        tools.replace_in_file(os.path.join(self._source_subfolder, "CMakeLists.txt"),
                              "TARGET_LINK_LIBRARIES(hiredis_ssl PRIVATE ${OPENSSL_LIBRARIES})",
                              "TARGET_LINK_LIBRARIES(hiredis_ssl PRIVATE OpenSSL::SSL)")
        cmake = self._configure_cmake()
        cmake.build()

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        self._cmake.definitions["ENABLE_SSL"] = self.options.with_ssl
        self._cmake.definitions["DISABLE_TESTS"] = True
        self._cmake.definitions["ENABLE_EXAMPLES"] = False
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def package(self):
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        tools.rmdir(os.path.join(self.package_folder, "share"))

    def package_info(self):
        # hiredis
        self.cpp_info.components["hiredislib"].names["cmake_find_package"] = "hiredis"
        self.cpp_info.components["hiredislib"].names["cmake_find_package_multi"] = "hiredis"
        self.cpp_info.components["hiredislib"].names["pkg_config"] = "hiredis"
        self.cpp_info.components["hiredislib"].libs = ["hiredis"]
        if self.settings.os == "Windows":
            self.cpp_info.components["hiredislib"].system_libs = ["ws2_32"]
        # hiredis_ssl
        if self.options.with_ssl:
            self.cpp_info.components["hiredis_ssl"].names["cmake_find_package"] = "hiredis_ssl"
            self.cpp_info.components["hiredis_ssl"].names["cmake_find_package_multi"] = "hiredis_ssl"
            self.cpp_info.components["hiredis_ssl"].names["pkg_config"] = "hiredis_ssl"
            self.cpp_info.components["hiredis_ssl"].libs = ["hiredis_ssl"]
            self.cpp_info.components["hiredis_ssl"].requires = ["hiredislib", "openssl::ssl"]
