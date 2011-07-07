cmake_minimum_required(VERSION 2.8)

set(APP_DIR "${CMAKE_SOURCE_DIR}/appengine")
set(APPENGINE_DIR "$ENV{HOME}/google_appengine" CACHE PATH "Appengine Python SDK directory")

set(ZIPS "")

macro(add_package generator name)
  foreach(version ${ARGN})
    string(REGEX REPLACE "[-./]" "_" safe_nameversion "${name}_${version}")
    set(zip_filename "${APP_DIR}/${safe_nameversion}.zip")
    set(js_filename "${APP_DIR}/static/data/${name}-${version}.js")
    set(target_name "${name}-${version}")

    add_custom_command(
      OUTPUT "${zip_filename}" "${js_filename}"
      COMMAND python "${CMAKE_SOURCE_DIR}/main.py" "${name}" "${version}"
      DEPENDS "${CMAKE_SOURCE_DIR}/generator_${generator}.py"
      WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
    )
    list(APPEND ZIPS "${zip_filename}")
  endforeach(version)
endmacro(add_package)

add_package(dbus dbus-python 0.84.0)
add_package(django django 1.3)
add_package(lxml lxml 2.3)
add_package(mysqlpython mysql-python 1.2.3)
add_package(paramiko paramiko 1.7.6)
add_package(pygobject pygobject 2.28.6)
add_package(pyinotify pyinotify 0.8.3 0.9.2)
add_package(python python 2.7.1)
add_package(simplejson simplejson 2.1.6)
add_package(sqlalchemy sqlalchemy 0.7.1)
add_package(tkinter tkinter 2.7.1)
add_package(twisted twisted 11.0.0)

add_library(dummy STATIC ${ZIPS})
set_target_properties(dummy PROPERTIES LINKER_LANGUAGE C)

add_custom_target(dev "${APPENGINE_DIR}/dev_appserver.py" "${APP_DIR}" DEPENDS dummy)
add_custom_target(update "${APPENGINE_DIR}/appcfg.py" update "${APP_DIR}" DEPENDS dummy)
