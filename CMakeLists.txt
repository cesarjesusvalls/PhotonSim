#----------------------------------------------------------------------------
# Setup the project
#
cmake_minimum_required(VERSION 3.16...3.27)
project(PhotonSim)

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
add_executable(PhotonSim PhotonSim.cc ${sources} ${headers})
target_include_directories(PhotonSim PRIVATE include ${ROOT_INCLUDE_DIRS})
target_link_libraries(PhotonSim PRIVATE ${Geant4_LIBRARIES} ${ROOT_LIBRARIES})

#----------------------------------------------------------------------------
# No additional scripts to copy for PhotonSim
#