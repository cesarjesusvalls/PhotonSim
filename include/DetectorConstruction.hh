//
// ********************************************************************
// * License and Disclaimer                                           *
// *                                                                  *
// * The  Geant4 software  is  copyright of the Copyright Holders  of *
// * the Geant4 Collaboration.  It is provided  under  the terms  and *
// * conditions of the Geant4 Software License,  included in the file *
// * LICENSE and available at  http://cern.ch/geant4/license .  These *
// * include a list of copyright holders.                             *
// *                                                                  *
// * Neither the authors of this software system, nor their employing *
// * institutes,nor the agencies providing financial support for this *
// * work  make  any representation or  warranty, express or implied, *
// * regarding  this  software system or assume any liability for its *
// * use.  Please see the license in the file  LICENSE  and URL above *
// * for the full disclaimer and the limitation of liability.         *
// *                                                                  *
// * This  code  implementation is the result of  the  scientific and *
// * technical work of the GEANT4 collaboration.                      *
// * By using,  copying,  modifying or  distributing the software (or *
// * any work based  on the software)  you  agree  to acknowledge its *
// * use  in  resulting  scientific  publications,  and indicate your *
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
//
/// \file OpticalPhotonDetector/include/DetectorConstruction.hh
/// \brief Definition of the OpticalPhotonDetector::DetectorConstruction class

#ifndef OpticalDetectorConstruction_h
#define OpticalDetectorConstruction_h 1

#include "G4VUserDetectorConstruction.hh"
#include "G4Material.hh"

class G4VPhysicalVolume;
class G4LogicalVolume;
class G4OpticalSurface;

namespace OpticalPhotonDetector
{

/// Detector construction class to define materials and geometry.
/// Creates a monolithic detector volume with configurable dimensions and material.

class DetectorConstruction : public G4VUserDetectorConstruction
{
  public:
    DetectorConstruction();
    ~DetectorConstruction() override = default;

    G4VPhysicalVolume* Construct() override;
    void ConstructSDandField() override;

    G4LogicalVolume* GetDetectorVolume() const { return fDetectorLogical; }
    
    // Configurable parameters
    void SetDetectorSize(G4double x, G4double y, G4double z);
    void SetDetectorMaterial(const G4String& materialName);

  private:
    void DefineMaterials();
    G4Material* ConstructWater();
    G4Material* ConstructLiquidArgon();
    G4Material* ConstructIce();
    G4Material* ConstructLiquidScintillator();
    
    G4LogicalVolume* fDetectorLogical = nullptr;
    
    // Detector parameters
    G4double fDetectorSizeX = 5.0*CLHEP::m;
    G4double fDetectorSizeY = 5.0*CLHEP::m;  
    G4double fDetectorSizeZ = 5.0*CLHEP::m;
    G4String fDetectorMaterialName = "Water";
    
    // Materials
    G4Material* fWater = nullptr;
    G4Material* fLiquidArgon = nullptr;
    G4Material* fIce = nullptr;
    G4Material* fLiquidScintillator = nullptr;
};

}  // namespace OpticalPhotonDetector

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#endif
