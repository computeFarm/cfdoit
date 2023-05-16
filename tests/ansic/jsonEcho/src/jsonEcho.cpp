
#include "jsonEcho.hpp"

#include "xeus/xhelper.hpp"

////////////////////////////////////////////////////////////////////////////
// Configure the interpreter...
//
void jsonEcho::JsonEcho::configure_impl(){
  // nothing to do....
}


////////////////////////////////////////////////////////////////////////////
// DO the request....
//
nl::json jsonEcho::JsonEcho::execute_request_impl(
    int executionCounter,
    const std::string& code,
    bool silent,
    bool storeHistory,
    nl::json userExpressions,
    bool allowStdIn  
) {

  auto errorType = "Unknown";
  auto errorMsg = std::stringstream();
  try {

    nl::json jData = nl::json::parse(code);

    nl::json publicData;
    publicData["text/plain"] = jData.dump(2);
    publish_execution_result(
      executionCounter,
      std::move(publicData),
      nl::json::object()
    );
    return xeus::create_successful_reply();

  } catch ( nl::json::parse_error& err ) {
    errorType = "Parse Error";
    errorMsg << "Parsing at: " << err.byte << std::endl;
    errorMsg << err.what() << std::endl;
  } catch ( std::exception& err ) {
    errorType = "General Error";
    errorMsg << err.what() << std::endl;
  } catch (...) {
    errorType = "Unknonwn Error";
    errorMsg << "Unknown erorr!" << std::endl ;
  }

  publish_execution_error(
    errorType,
    errorMsg.str(),
    nl::json::array()
  );
  return xeus::create_error_reply();
}

////////////////////////////////////////////////////////////////////////////
// Provide the user with some code completion information 
// at the cursor position...
//
nl::json jsonEcho::JsonEcho::complete_request_impl(
  const std::string& code,
  int cursorPos  
) {
  return xeus::create_complete_reply({}, cursorPos, cursorPos);
}

////////////////////////////////////////////////////////////////////////////
// Inspect the request at the cursor position ...
//
nl::json jsonEcho::JsonEcho::inspect_request_impl(
  const std::string& code,
  int cursorPos,
  int detailLevel  
) {
  return xeus::create_inspect_reply();
}

////////////////////////////////////////////////////////////////////////////
// Tell the user if the code is "complete"...
//
nl::json jsonEcho::JsonEcho::is_complete_request_impl(
  const std::string& code
) {
  try {

    nl::json jData = nl::json::parse(code);

    return xeus::create_is_complete_reply("complete");
  } catch ( nl::json::parse_error& err ) {
    return xeus::create_is_complete_reply("incomplete");
  } catch (...) {
  }  
  return xeus::create_is_complete_reply("invalid");
}

////////////////////////////////////////////////////////////////////////////
// Return the JsonEcho kernel information
//
nl::json jsonEcho::JsonEcho::kernel_info_request_impl() {
  return xeus::create_info_reply(
    "",
    "JsonEcho",
    "0.0.1",
    "JoyLoL-JSON",
    "0.0.1",
    "text/x-json",
    ".json",
    "JsonLexer",
    "json"
  );
}

////////////////////////////////////////////////////////////////////////////
// Shutdown this kernel!
//
void jsonEcho::JsonEcho::shutdown_request_impl() {
  std::cout << "Bye!" << std::endl;
}
