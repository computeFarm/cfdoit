# Xeus-JSON (echo) kernel

This is a simple "Hello World" [Jupyter](https://jupyter.org/) Kernel
implemented in [Xeus](https://xeus.readthedocs.io/en/latest/).

To provide an interface with any eventual JoyLoL backend "test" methods,
we start with a very simple JSON echo function. This kernel expects JSON
structures in a C-String as the "code". These JSON structures are parsed
and then printed and sent back to the user (unchanged).

This echo kernel depends upon the following libraries:

1. [xeus](https://github.com/jupyter-xeus/xeus) (compiled C++)

2. [xtl](https://github.com/xtensor-stack/xtl) (C++ header)

3. [nolhmann_json](https://github.com/nlohmann/json) (C++ header)

4. [xeus-zmq](https://github.com/jupyter-xeus/xeus-zmq) (compiled C++)

5. [ZeroMQ](https://github.com/zeromq/libzmq) (compiled C++)

6. [cppzmq](https://github.com/zeromq/cppzmq) (C++ header)

7. [OpenSSL](https://github.com/openssl/openssl) (typcially a linux system
   package)

We use the [Ninja build system](https://ninja-build.org/) to build the overall
system (compiled dependencies as well as the JSON-echo kernel).

System requirements:

1. curl

2. g++/gcc or clang

3. make/gnumake and cmake

4. libssl-dev

5. uuid-dev (libuuid)

# NOTES

We want to split the download and build phases... using python generator?

In the explicit download phase, since we use build statments with no explicit
inputs, the packages are always downloaded.

To prevent this repeated downloading, we explicitly separate the download phase
and the build phase.

## Testing

We use
[jupyter_kernel_test](https://github.com/jupyter/jupyter_kernel_test) to
provide a simple external test of our jupyter kernel.

