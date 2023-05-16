#ifndef JSON_ECHO_HPP
#define JSON_ECHO_HPP

#include "xeus/xinterpreter.hpp"

#include "nlohmann/json.hpp"

namespace nl = nlohmann;

namespace jsonEcho {

  class JsonEcho : public xeus::xinterpreter {

  public:

    JsonEcho() = default;
    virtual ~JsonEcho() = default;

  private:

    void configure_impl() override;

    nl::json execute_request_impl(
      int executionCounter,
      const std::string& code,
      bool silent,
      bool storeHistory,
      nl::json userExpressions,
      bool allowStdIn
    ) override;

  nl::json complete_request_impl(
    const std::string& code,
    int cursorPos
  ) override;

  nl::json inspect_request_impl(
    const std::string& code,
    int cursorPos,
    int detailLevel
  ) override;

  nl::json is_complete_request_impl(
    const std::string& code
  ) override;

  nl::json kernel_info_request_impl() override;

  void shutdown_request_impl() override;

  };

}

#endif