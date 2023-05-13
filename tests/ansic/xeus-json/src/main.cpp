#include <memory>

#include "xeus/xkernel.hpp"
#include "xeus/xkernel_configuration.hpp"
#include "xeus-zmq/xserver_zmq.hpp"

#include "jsonEcho.hpp"

int main(int argc, char* argv[]) {
  std::string fileName = (argc == 1) ? "connection.json" : argv[2];
  xeus::xconfiguration config = xeus::load_configuration(fileName);

  auto context = xeus::make_context<zmq::context_t>();

  using interpreter_ptr = std::unique_ptr<jsonEcho::JsonEcho>;
  interpreter_ptr interpreter = interpreter_ptr(new jsonEcho::JsonEcho());

  xeus::xkernel kernel(
    config, xeus::get_user_name(), 
    std::move(context), std::move(interpreter),
    xeus::make_xserver_zmq
  );
  kernel.start();

  return 0;
}