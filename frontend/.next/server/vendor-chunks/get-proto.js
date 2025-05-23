"use strict";
/*
 * ATTENTION: An "eval-source-map" devtool has been used.
 * This devtool is neither made for production nor for readable output files.
 * It uses "eval()" calls to create a separate source file with attached SourceMaps in the browser devtools.
 * If you are trying to read the output file, select a different devtool (https://webpack.js.org/configuration/devtool/)
 * or disable the default devtool with "devtool: false".
 * If you are looking for production-ready output files, see mode: "production" (https://webpack.js.org/configuration/mode/).
 */
exports.id = "vendor-chunks/get-proto";
exports.ids = ["vendor-chunks/get-proto"];
exports.modules = {

/***/ "(ssr)/./node_modules/get-proto/Object.getPrototypeOf.js":
/*!*********************************************************!*\
  !*** ./node_modules/get-proto/Object.getPrototypeOf.js ***!
  \*********************************************************/
/***/ ((module, __unused_webpack_exports, __webpack_require__) => {

eval("\nvar $Object = __webpack_require__(/*! es-object-atoms */ \"(ssr)/./node_modules/es-object-atoms/index.js\");\n/** @type {import('./Object.getPrototypeOf')} */ module.exports = $Object.getPrototypeOf || null;\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHNzcikvLi9ub2RlX21vZHVsZXMvZ2V0LXByb3RvL09iamVjdC5nZXRQcm90b3R5cGVPZi5qcyIsIm1hcHBpbmdzIjoiQUFBQTtBQUVBLElBQUlBLFVBQVVDLG1CQUFPQSxDQUFDO0FBRXRCLDhDQUE4QyxHQUM5Q0MsT0FBT0MsT0FBTyxHQUFHSCxRQUFRSSxjQUFjLElBQUkiLCJzb3VyY2VzIjpbIndlYnBhY2s6Ly9jYXJib25waWxvdC1mcm9udGVuZC8uL25vZGVfbW9kdWxlcy9nZXQtcHJvdG8vT2JqZWN0LmdldFByb3RvdHlwZU9mLmpzP2ZiMzciXSwic291cmNlc0NvbnRlbnQiOlsiJ3VzZSBzdHJpY3QnO1xyXG5cclxudmFyICRPYmplY3QgPSByZXF1aXJlKCdlcy1vYmplY3QtYXRvbXMnKTtcclxuXHJcbi8qKiBAdHlwZSB7aW1wb3J0KCcuL09iamVjdC5nZXRQcm90b3R5cGVPZicpfSAqL1xyXG5tb2R1bGUuZXhwb3J0cyA9ICRPYmplY3QuZ2V0UHJvdG90eXBlT2YgfHwgbnVsbDtcclxuIl0sIm5hbWVzIjpbIiRPYmplY3QiLCJyZXF1aXJlIiwibW9kdWxlIiwiZXhwb3J0cyIsImdldFByb3RvdHlwZU9mIl0sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///(ssr)/./node_modules/get-proto/Object.getPrototypeOf.js\n");

/***/ }),

/***/ "(ssr)/./node_modules/get-proto/Reflect.getPrototypeOf.js":
/*!**********************************************************!*\
  !*** ./node_modules/get-proto/Reflect.getPrototypeOf.js ***!
  \**********************************************************/
/***/ ((module) => {

eval("\n/** @type {import('./Reflect.getPrototypeOf')} */ module.exports = typeof Reflect !== \"undefined\" && Reflect.getPrototypeOf || null;\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHNzcikvLi9ub2RlX21vZHVsZXMvZ2V0LXByb3RvL1JlZmxlY3QuZ2V0UHJvdG90eXBlT2YuanMiLCJtYXBwaW5ncyI6IkFBQUE7QUFFQSwrQ0FBK0MsR0FDL0NBLE9BQU9DLE9BQU8sR0FBRyxPQUFRQyxZQUFZLGVBQWVBLFFBQVFDLGNBQWMsSUFBSyIsInNvdXJjZXMiOlsid2VicGFjazovL2NhcmJvbnBpbG90LWZyb250ZW5kLy4vbm9kZV9tb2R1bGVzL2dldC1wcm90by9SZWZsZWN0LmdldFByb3RvdHlwZU9mLmpzPzNiMjUiXSwic291cmNlc0NvbnRlbnQiOlsiJ3VzZSBzdHJpY3QnO1xyXG5cclxuLyoqIEB0eXBlIHtpbXBvcnQoJy4vUmVmbGVjdC5nZXRQcm90b3R5cGVPZicpfSAqL1xyXG5tb2R1bGUuZXhwb3J0cyA9ICh0eXBlb2YgUmVmbGVjdCAhPT0gJ3VuZGVmaW5lZCcgJiYgUmVmbGVjdC5nZXRQcm90b3R5cGVPZikgfHwgbnVsbDtcclxuIl0sIm5hbWVzIjpbIm1vZHVsZSIsImV4cG9ydHMiLCJSZWZsZWN0IiwiZ2V0UHJvdG90eXBlT2YiXSwic291cmNlUm9vdCI6IiJ9\n//# sourceURL=webpack-internal:///(ssr)/./node_modules/get-proto/Reflect.getPrototypeOf.js\n");

/***/ }),

/***/ "(ssr)/./node_modules/get-proto/index.js":
/*!*****************************************!*\
  !*** ./node_modules/get-proto/index.js ***!
  \*****************************************/
/***/ ((module, __unused_webpack_exports, __webpack_require__) => {

eval("\nvar reflectGetProto = __webpack_require__(/*! ./Reflect.getPrototypeOf */ \"(ssr)/./node_modules/get-proto/Reflect.getPrototypeOf.js\");\nvar originalGetProto = __webpack_require__(/*! ./Object.getPrototypeOf */ \"(ssr)/./node_modules/get-proto/Object.getPrototypeOf.js\");\nvar getDunderProto = __webpack_require__(/*! dunder-proto/get */ \"(ssr)/./node_modules/dunder-proto/get.js\");\n/** @type {import('.')} */ module.exports = reflectGetProto ? function getProto(O) {\n    // @ts-expect-error TS can't narrow inside a closure, for some reason\n    return reflectGetProto(O);\n} : originalGetProto ? function getProto(O) {\n    if (!O || typeof O !== \"object\" && typeof O !== \"function\") {\n        throw new TypeError(\"getProto: not an object\");\n    }\n    // @ts-expect-error TS can't narrow inside a closure, for some reason\n    return originalGetProto(O);\n} : getDunderProto ? function getProto(O) {\n    // @ts-expect-error TS can't narrow inside a closure, for some reason\n    return getDunderProto(O);\n} : null;\n//# sourceURL=[module]\n//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJmaWxlIjoiKHNzcikvLi9ub2RlX21vZHVsZXMvZ2V0LXByb3RvL2luZGV4LmpzIiwibWFwcGluZ3MiOiJBQUFBO0FBRUEsSUFBSUEsa0JBQWtCQyxtQkFBT0EsQ0FBQztBQUM5QixJQUFJQyxtQkFBbUJELG1CQUFPQSxDQUFDO0FBRS9CLElBQUlFLGlCQUFpQkYsbUJBQU9BLENBQUM7QUFFN0Isd0JBQXdCLEdBQ3hCRyxPQUFPQyxPQUFPLEdBQUdMLGtCQUNkLFNBQVNNLFNBQVNDLENBQUM7SUFDcEIscUVBQXFFO0lBQ3JFLE9BQU9QLGdCQUFnQk87QUFDeEIsSUFDRUwsbUJBQ0MsU0FBU0ksU0FBU0MsQ0FBQztJQUNwQixJQUFJLENBQUNBLEtBQU0sT0FBT0EsTUFBTSxZQUFZLE9BQU9BLE1BQU0sWUFBYTtRQUM3RCxNQUFNLElBQUlDLFVBQVU7SUFDckI7SUFDQSxxRUFBcUU7SUFDckUsT0FBT04saUJBQWlCSztBQUN6QixJQUNFSixpQkFDQyxTQUFTRyxTQUFTQyxDQUFDO0lBQ3BCLHFFQUFxRTtJQUNyRSxPQUFPSixlQUFlSTtBQUN2QixJQUNFIiwic291cmNlcyI6WyJ3ZWJwYWNrOi8vY2FyYm9ucGlsb3QtZnJvbnRlbmQvLi9ub2RlX21vZHVsZXMvZ2V0LXByb3RvL2luZGV4LmpzPzVhMTMiXSwic291cmNlc0NvbnRlbnQiOlsiJ3VzZSBzdHJpY3QnO1xyXG5cclxudmFyIHJlZmxlY3RHZXRQcm90byA9IHJlcXVpcmUoJy4vUmVmbGVjdC5nZXRQcm90b3R5cGVPZicpO1xyXG52YXIgb3JpZ2luYWxHZXRQcm90byA9IHJlcXVpcmUoJy4vT2JqZWN0LmdldFByb3RvdHlwZU9mJyk7XHJcblxyXG52YXIgZ2V0RHVuZGVyUHJvdG8gPSByZXF1aXJlKCdkdW5kZXItcHJvdG8vZ2V0Jyk7XHJcblxyXG4vKiogQHR5cGUge2ltcG9ydCgnLicpfSAqL1xyXG5tb2R1bGUuZXhwb3J0cyA9IHJlZmxlY3RHZXRQcm90b1xyXG5cdD8gZnVuY3Rpb24gZ2V0UHJvdG8oTykge1xyXG5cdFx0Ly8gQHRzLWV4cGVjdC1lcnJvciBUUyBjYW4ndCBuYXJyb3cgaW5zaWRlIGEgY2xvc3VyZSwgZm9yIHNvbWUgcmVhc29uXHJcblx0XHRyZXR1cm4gcmVmbGVjdEdldFByb3RvKE8pO1xyXG5cdH1cclxuXHQ6IG9yaWdpbmFsR2V0UHJvdG9cclxuXHRcdD8gZnVuY3Rpb24gZ2V0UHJvdG8oTykge1xyXG5cdFx0XHRpZiAoIU8gfHwgKHR5cGVvZiBPICE9PSAnb2JqZWN0JyAmJiB0eXBlb2YgTyAhPT0gJ2Z1bmN0aW9uJykpIHtcclxuXHRcdFx0XHR0aHJvdyBuZXcgVHlwZUVycm9yKCdnZXRQcm90bzogbm90IGFuIG9iamVjdCcpO1xyXG5cdFx0XHR9XHJcblx0XHRcdC8vIEB0cy1leHBlY3QtZXJyb3IgVFMgY2FuJ3QgbmFycm93IGluc2lkZSBhIGNsb3N1cmUsIGZvciBzb21lIHJlYXNvblxyXG5cdFx0XHRyZXR1cm4gb3JpZ2luYWxHZXRQcm90byhPKTtcclxuXHRcdH1cclxuXHRcdDogZ2V0RHVuZGVyUHJvdG9cclxuXHRcdFx0PyBmdW5jdGlvbiBnZXRQcm90byhPKSB7XHJcblx0XHRcdFx0Ly8gQHRzLWV4cGVjdC1lcnJvciBUUyBjYW4ndCBuYXJyb3cgaW5zaWRlIGEgY2xvc3VyZSwgZm9yIHNvbWUgcmVhc29uXHJcblx0XHRcdFx0cmV0dXJuIGdldER1bmRlclByb3RvKE8pO1xyXG5cdFx0XHR9XHJcblx0XHRcdDogbnVsbDtcclxuIl0sIm5hbWVzIjpbInJlZmxlY3RHZXRQcm90byIsInJlcXVpcmUiLCJvcmlnaW5hbEdldFByb3RvIiwiZ2V0RHVuZGVyUHJvdG8iLCJtb2R1bGUiLCJleHBvcnRzIiwiZ2V0UHJvdG8iLCJPIiwiVHlwZUVycm9yIl0sInNvdXJjZVJvb3QiOiIifQ==\n//# sourceURL=webpack-internal:///(ssr)/./node_modules/get-proto/index.js\n");

/***/ })

};
;