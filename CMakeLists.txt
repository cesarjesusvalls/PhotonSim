#----------------------------------------------------------------------------
# Setup the project
#
cmake_minimum_required(VERSION 3.16...3.27)
project(OpticalPhotonDetector)

#----------------------------------------------------------------------------
# Find Geant4 package, activating all available UI and Vis drivers by default
#
find_package(Geant4 REQUIRED ui_all vis_all)

#----------------------------------------------------------------------------
# Find ROOT package
#
find_package(ROOT REQUIRED COMPONENTS Core Tree)

#----------------------------------------------------------------------------
# Locate sources and headers for this project
#
file(GLOB sources ${PROJECT_SOURCE_DIR}/src/*.cc)
file(GLOB headers ${PROJECT_SOURCE_DIR}/include/*.hh)

#----------------------------------------------------------------------------
# Add the executable, use our local headers, and link it to the Geant4 and ROOT libraries
#
add_executable(OpticalPhotonDetector OpticalPhotonDetector.cc ${sources} ${headers})
target_include_directories(OpticalPhotonDetector PRIVATE include ${ROOT_INCLUDE_DIRS})
target_link_libraries(OpticalPhotonDetector PRIVATE ${Geant4_LIBRARIES} ${ROOT_LIBRARIES})

#----------------------------------------------------------------------------
# Copy all scripts to the build directory
#
set(PROJECT_SCRIPTS
  init_vis.mac
  run1.mac
  run2.mac
  vis.mac
  )

foreach(_script ${PROJECT_SCRIPTS})
  configure_file(
    ${PROJECT_SOURCE_DIR}/${_script}
    ${PROJECT_BINARY_DIR}/${_script}
    COPYONLY
    )
endforeach()