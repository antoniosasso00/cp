"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
exports.id = "vendor-chunks/raf-schd";
exports.ids = ["vendor-chunks/raf-schd"];
exports.modules = {

/***/ "(ssr)/./node_modules/raf-schd/dist/raf-schd.esm.js":
/*!****************************************************!*\
  !*** ./node_modules/raf-schd/dist/raf-schd.esm.js ***!
  \****************************************************/
/***/ ((__unused_webpack_module, __webpack_exports__, __webpack_require__) => {

eval("__webpack_require__.r(__webpack_exports__);\n/* harmony export */ __webpack_require__.d(__webpack_exports__, {\n/* harmony export */   \"default\": () => (__WEBPACK_DEFAULT_EXPORT__)\n/* harmony export */ });\nvar rafSchd = function rafSchd(fn) {\n    var lastArgs = [];\n    var frameId = null;\n    var wrapperFn = function wrapperFn() {\n        for(var _len = arguments.length, args = new Array(_len), _key = 0; _key < _len; _key++){\n            args[_key] = arguments[_key];\n        }\n        lastArgs = args;\n        if (frameId) {\n            return;\n        }\n        frameId = requestAnimationFrame(function() {\n            frameId = null;\n            fn.apply(void 0, lastArgs);\n        });\n    };\n    wrapperFn.cancel = function() {\n        if (!frameId) {\n            return;\n        }\n        cancelAnimationFrame(frameId);\n        frameId = null;\n    };\n    return wrapperFn;\n};\n/* harmony default export */ const __WEBPACK_DEFAULT_EXPORT__ = (rafSchd);\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHNzcikvLi9ub2RlX21vZHVsZXMvcmFmLXNjaGQvZGlzdC9yYWYtc2NoZC5lc20uanMiLCJtYXBwaW5ncyI6Ijs7OztBQUFBLElBQUlBLFVBQVUsU0FBU0EsUUFBUUMsRUFBRTtJQUMvQixJQUFJQyxXQUFXLEVBQUU7SUFDakIsSUFBSUMsVUFBVTtJQUVkLElBQUlDLFlBQVksU0FBU0E7UUFDdkIsSUFBSyxJQUFJQyxPQUFPQyxVQUFVQyxNQUFNLEVBQUVDLE9BQU8sSUFBSUMsTUFBTUosT0FBT0ssT0FBTyxHQUFHQSxPQUFPTCxNQUFNSyxPQUFRO1lBQ3ZGRixJQUFJLENBQUNFLEtBQUssR0FBR0osU0FBUyxDQUFDSSxLQUFLO1FBQzlCO1FBRUFSLFdBQVdNO1FBRVgsSUFBSUwsU0FBUztZQUNYO1FBQ0Y7UUFFQUEsVUFBVVEsc0JBQXNCO1lBQzlCUixVQUFVO1lBQ1ZGLEdBQUdXLEtBQUssQ0FBQyxLQUFLLEdBQUdWO1FBQ25CO0lBQ0Y7SUFFQUUsVUFBVVMsTUFBTSxHQUFHO1FBQ2pCLElBQUksQ0FBQ1YsU0FBUztZQUNaO1FBQ0Y7UUFFQVcscUJBQXFCWDtRQUNyQkEsVUFBVTtJQUNaO0lBRUEsT0FBT0M7QUFDVDtBQUVBLGlFQUFlSixPQUFPQSxFQUFDIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vY2FyYm9ucGlsb3QtZnJvbnRlbmQvLi9ub2RlX21vZHVsZXMvcmFmLXNjaGQvZGlzdC9yYWYtc2NoZC5lc20uanM/OGFjZSJdLCJzb3VyY2VzQ29udGVudCI6WyJ2YXIgcmFmU2NoZCA9IGZ1bmN0aW9uIHJhZlNjaGQoZm4pIHtcbiAgdmFyIGxhc3RBcmdzID0gW107XG4gIHZhciBmcmFtZUlkID0gbnVsbDtcblxuICB2YXIgd3JhcHBlckZuID0gZnVuY3Rpb24gd3JhcHBlckZuKCkge1xuICAgIGZvciAodmFyIF9sZW4gPSBhcmd1bWVudHMubGVuZ3RoLCBhcmdzID0gbmV3IEFycmF5KF9sZW4pLCBfa2V5ID0gMDsgX2tleSA8IF9sZW47IF9rZXkrKykge1xuICAgICAgYXJnc1tfa2V5XSA9IGFyZ3VtZW50c1tfa2V5XTtcbiAgICB9XG5cbiAgICBsYXN0QXJncyA9IGFyZ3M7XG5cbiAgICBpZiAoZnJhbWVJZCkge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIGZyYW1lSWQgPSByZXF1ZXN0QW5pbWF0aW9uRnJhbWUoZnVuY3Rpb24gKCkge1xuICAgICAgZnJhbWVJZCA9IG51bGw7XG4gICAgICBmbi5hcHBseSh2b2lkIDAsIGxhc3RBcmdzKTtcbiAgICB9KTtcbiAgfTtcblxuICB3cmFwcGVyRm4uY2FuY2VsID0gZnVuY3Rpb24gKCkge1xuICAgIGlmICghZnJhbWVJZCkge1xuICAgICAgcmV0dXJuO1xuICAgIH1cblxuICAgIGNhbmNlbEFuaW1hdGlvbkZyYW1lKGZyYW1lSWQpO1xuICAgIGZyYW1lSWQgPSBudWxsO1xuICB9O1xuXG4gIHJldHVybiB3cmFwcGVyRm47XG59O1xuXG5leHBvcnQgZGVmYXVsdCByYWZTY2hkO1xuIl0sIm5hbWVzIjpbInJhZlNjaGQiLCJmbiIsImxhc3RBcmdzIiwiZnJhbWVJZCIsIndyYXBwZXJGbiIsIl9sZW4iLCJhcmd1bWVudHMiLCJsZW5ndGgiLCJhcmdzIiwiQXJyYXkiLCJfa2V5IiwicmVxdWVzdEFuaW1hdGlvbkZyYW1lIiwiYXBwbHkiLCJjYW5jZWwiLCJjYW5jZWxBbmltYXRpb25GcmFtZSJdLCJzb3VyY2VSb290IjoiIn0=\n//# sourceURL=webpack-internal:///(ssr)/./node_modules/raf-schd/dist/raf-schd.esm.js\n");

/***/ })

};
;