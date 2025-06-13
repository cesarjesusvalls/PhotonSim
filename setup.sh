#!/bin/bash
# PhotonSim Setup Script
# This script sets up the environment for building and running PhotonSim

# Set the GEANT4 installation path
export GEANT4_INSTALL_DIR="/Users/cjesus/Software/geant4-install"

# Add GEANT4 to CMAKE_PREFIX_PATH for building
export CMAKE_PREFIX_PATH="${GEANT4_INSTALL_DIR}:$CMAKE_PREFIX_PATH"

# Add GEANT4 libraries to library path for runtime
export DYLD_LIBRARY_PATH="${GEANT4_INSTALL_DIR}/lib:$DYLD_LIBRARY_PATH"

# Add GEANT4 binaries to PATH
export PATH="${GEANT4_INSTALL_DIR}/bin:$PATH"

# Set GEANT4 data directories (if needed)
export G4LEVELGAMMADATA="${GEANT4_INSTALL_DIR}/share/Geant4/data/PhotonEvaporation5.7"
export G4RADIOACTIVEDATA="${GEANT4_INSTALL_DIR}/share/Geant4/data/RadioactiveDecay5.6"
export G4PARTICLEXSDATA="${GEANT4_INSTALL_DIR}/share/Geant4/data/G4PARTICLEXS4.0"
export G4PIIDATA="${GEANT4_INSTALL_DIR}/share/Geant4/data/G4PII1.3"
export G4REALSURFACEDATA="${GEANT4_INSTALL_DIR}/share/Geant4/data/RealSurface2.2"
export G4SAIDXSDATA="${GEANT4_INSTALL_DIR}/share/Geant4/data/G4SAIDDATA2.0"
export G4ABLADATA="${GEANT4_INSTALL_DIR}/share/Geant4/data/G4ABLA3.1"
export G4INCLDATA="${GEANT4_INSTALL_DIR}/share/Geant4/data/G4INCL1.0"
export G4ENSDFSTATEDATA="${GEANT4_INSTALL_DIR}/share/Geant4/data/G4ENSDFSTATE2.3"

echo "PhotonSim environment setup complete!"
echo "GEANT4 installation: ${GEANT4_INSTALL_DIR}"
echo ""
echo "To build PhotonSim:"
echo "  cd build"
echo "  cmake .. && make -j4"
echo ""
echo "To run PhotonSim:"
echo "  ./PhotonSim [macro_file]"