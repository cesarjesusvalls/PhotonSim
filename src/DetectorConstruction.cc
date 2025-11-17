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
/// \file PhotonSim/src/DetectorConstruction.cc
/// \brief Implementation of the PhotonSim::DetectorConstruction class

#include "DetectorConstruction.hh"

#include "G4Box.hh"
#include "G4LogicalVolume.hh"
#include "G4NistManager.hh"
#include "G4PVPlacement.hh"
#include "G4SystemOfUnits.hh"
#include "G4PhysicalConstants.hh"
#include "G4Material.hh"
#include "G4MaterialPropertiesTable.hh"
#include "G4OpticalSurface.hh"
#include "G4LogicalSkinSurface.hh"

namespace PhotonSim
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

DetectorConstruction::DetectorConstruction()
{
  DefineMaterials();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DetectorConstruction::DefineMaterials()
{
  G4NistManager* nist = G4NistManager::Instance();

  // Water with optical properties
  fWater = ConstructWater();

  // Liquid Argon with optical properties
  fLiquidArgon = ConstructLiquidArgon();

  // Ice with optical properties
  fIce = ConstructIce();

  // Liquid Scintillator with optical properties
  fLiquidScintillator = ConstructLiquidScintillator();

  // Liquid Hydrogen with optical properties
  fLiquidHydrogen = ConstructHydrogen();

  // Liquid Oxygen with optical properties
  fLiquidOxygen = ConstructOxygen();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4Material* DetectorConstruction::ConstructWater()
{
  G4NistManager* nist = G4NistManager::Instance();
  G4Material* water = nist->FindOrBuildMaterial("G4_WATER");
  
  // Water optical properties
  G4MaterialPropertiesTable* waterMPT = new G4MaterialPropertiesTable();
  
  // Photon energies (wavelengths from 200-700 nm)
  const G4int nEntries = 10;
  G4double photonEnergy[nEntries] = {
    1.77*eV, 2.07*eV, 2.48*eV, 2.76*eV, 3.10*eV,
    3.54*eV, 4.13*eV, 4.96*eV, 5.64*eV, 6.20*eV
  };
  
  // Refractive index of water
  G4double refractiveIndex[nEntries] = {
    1.333, 1.334, 1.335, 1.337, 1.338,
    1.340, 1.343, 1.347, 1.351, 1.358
  };
  
  // Absorption length of water (in meters)
  G4double absorption[nEntries] = {
    35.*m, 35.*m, 35.*m, 35.*m, 35.*m,
    35.*m, 35.*m, 35.*m, 35.*m, 35.*m
  };
  
  waterMPT->AddProperty("RINDEX", photonEnergy, refractiveIndex, nEntries);
  waterMPT->AddProperty("ABSLENGTH", photonEnergy, absorption, nEntries);
  
  water->SetMaterialPropertiesTable(waterMPT);
  
  return water;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4Material* DetectorConstruction::ConstructLiquidArgon()
{
  G4NistManager* nist = G4NistManager::Instance();
  G4Element* Ar = nist->FindOrBuildElement("Ar");
  
  G4Material* liquidAr = new G4Material("LiquidArgon", 1.40*g/cm3, 1, kStateLiquid, 87*kelvin);
  liquidAr->AddElement(Ar, 1);
  
  // Liquid Argon optical properties
  G4MaterialPropertiesTable* larMPT = new G4MaterialPropertiesTable();
  
  const G4int nEntries = 10;
  G4double photonEnergy[nEntries] = {
    6.5*eV, 7.0*eV, 7.5*eV, 8.0*eV, 8.5*eV,
    9.0*eV, 9.5*eV, 10.0*eV, 10.5*eV, 11.0*eV
  };
  
  // Refractive index of liquid argon
  G4double refractiveIndex[nEntries] = {
    1.232, 1.236, 1.240, 1.245, 1.250,
    1.256, 1.262, 1.269, 1.277, 1.285
  };
  
  // Rayleigh scattering length
  G4double rayleigh[nEntries] = {
    55.*cm, 55.*cm, 55.*cm, 55.*cm, 55.*cm,
    55.*cm, 55.*cm, 55.*cm, 55.*cm, 55.*cm
  };
  
  larMPT->AddProperty("RINDEX", photonEnergy, refractiveIndex, nEntries);
  larMPT->AddProperty("RAYLEIGH", photonEnergy, rayleigh, nEntries);
  
  liquidAr->SetMaterialPropertiesTable(larMPT);
  
  return liquidAr;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4Material* DetectorConstruction::ConstructIce()
{
  G4NistManager* nist = G4NistManager::Instance();
  G4Element* H = nist->FindOrBuildElement("H");
  G4Element* O = nist->FindOrBuildElement("O");
  
  G4Material* ice = new G4Material("Ice", 0.92*g/cm3, 2, kStateSolid, 263*kelvin);
  ice->AddElement(H, 2);
  ice->AddElement(O, 1);
  
  // Ice optical properties
  G4MaterialPropertiesTable* iceMPT = new G4MaterialPropertiesTable();
  
  const G4int nEntries = 10;
  G4double photonEnergy[nEntries] = {
    1.77*eV, 2.07*eV, 2.48*eV, 2.76*eV, 3.10*eV,
    3.54*eV, 4.13*eV, 4.96*eV, 5.64*eV, 6.20*eV
  };
  
  // Refractive index of ice
  G4double refractiveIndex[nEntries] = {
    1.31, 1.31, 1.31, 1.31, 1.31,
    1.31, 1.31, 1.31, 1.31, 1.31
  };
  
  // Absorption length of ice
  G4double absorption[nEntries] = {
    100.*m, 100.*m, 100.*m, 100.*m, 100.*m,
    100.*m, 100.*m, 100.*m, 100.*m, 100.*m
  };
  
  iceMPT->AddProperty("RINDEX", photonEnergy, refractiveIndex, nEntries);
  iceMPT->AddProperty("ABSLENGTH", photonEnergy, absorption, nEntries);
  
  ice->SetMaterialPropertiesTable(iceMPT);
  
  return ice;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4Material* DetectorConstruction::ConstructLiquidScintillator()
{
  G4NistManager* nist = G4NistManager::Instance();
  G4Element* C = nist->FindOrBuildElement("C");
  G4Element* H = nist->FindOrBuildElement("H");
  
  G4Material* scintillator = new G4Material("LiquidScintillator", 0.86*g/cm3, 2);
  scintillator->AddElement(C, 9);
  scintillator->AddElement(H, 10);
  
  // Liquid Scintillator optical properties
  G4MaterialPropertiesTable* scintMPT = new G4MaterialPropertiesTable();
  
  const G4int nEntries = 10;
  G4double photonEnergy[nEntries] = {
    1.77*eV, 2.07*eV, 2.48*eV, 2.76*eV, 3.10*eV,
    3.54*eV, 4.13*eV, 4.96*eV, 5.64*eV, 6.20*eV
  };
  
  // Refractive index of liquid scintillator
  G4double refractiveIndex[nEntries] = {
    1.47, 1.47, 1.47, 1.47, 1.47,
    1.47, 1.47, 1.47, 1.47, 1.47
  };
  
  // Absorption length
  G4double absorption[nEntries] = {
    10.*m, 10.*m, 10.*m, 10.*m, 10.*m,
    10.*m, 10.*m, 10.*m, 10.*m, 10.*m
  };
  
  // Scintillation properties
  G4double scintillationYield[nEntries] = {
    10000./MeV, 10000./MeV, 10000./MeV, 10000./MeV, 10000./MeV,
    10000./MeV, 10000./MeV, 10000./MeV, 10000./MeV, 10000./MeV
  };
  
  scintMPT->AddProperty("RINDEX", photonEnergy, refractiveIndex, nEntries);
  scintMPT->AddProperty("ABSLENGTH", photonEnergy, absorption, nEntries);
  scintMPT->AddConstProperty("SCINTILLATIONYIELD", 10000./MeV);
  scintMPT->AddConstProperty("RESOLUTIONSCALE", 1.0);
  scintMPT->AddConstProperty("SCINTILLATIONTIMECONSTANT1", 10.*ns);
  scintMPT->AddConstProperty("SCINTILLATIONTIMECONSTANT2", 50.*ns);
  scintMPT->AddConstProperty("SCINTILLATIONYIELD1", 0.8);
  scintMPT->AddConstProperty("SCINTILLATIONYIELD2", 0.2);
  
  scintillator->SetMaterialPropertiesTable(scintMPT);

  return scintillator;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4Material* DetectorConstruction::ConstructHydrogen()
{
  // Liquid hydrogen at 20K
  G4double density = 0.071*g/cm3;
  G4Material* liquidH2 = new G4Material("LiquidHydrogen", density, 1);
  G4Element* H = G4NistManager::Instance()->FindOrBuildElement("H");
  liquidH2->AddElement(H, 2);  // H2 molecules

  // Liquid hydrogen optical properties
  G4MaterialPropertiesTable* h2MPT = new G4MaterialPropertiesTable();

  // Photon energies (wavelengths from 200-700 nm)
  const G4int nEntries = 10;
  G4double photonEnergy[nEntries] = {
    1.77*eV, 2.07*eV, 2.48*eV, 2.76*eV, 3.10*eV,
    3.54*eV, 4.13*eV, 4.96*eV, 5.64*eV, 6.20*eV
  };

  // Refractive index of liquid hydrogen (~1.11)
  G4double refractiveIndex[nEntries] = {
    1.110, 1.110, 1.111, 1.111, 1.112,
    1.112, 1.113, 1.114, 1.115, 1.116
  };

  // Absorption length (very transparent, ~10m)
  G4double absorption[nEntries] = {
    10.*m, 10.*m, 10.*m, 10.*m, 10.*m,
    10.*m, 10.*m, 10.*m, 10.*m, 10.*m
  };

  h2MPT->AddProperty("RINDEX", photonEnergy, refractiveIndex, nEntries);
  h2MPT->AddProperty("ABSLENGTH", photonEnergy, absorption, nEntries);

  liquidH2->SetMaterialPropertiesTable(h2MPT);

  return liquidH2;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4Material* DetectorConstruction::ConstructOxygen()
{
  // Liquid oxygen at 90K
  G4double density = 1.141*g/cm3;
  G4Material* liquidO2 = new G4Material("LiquidOxygen", density, 1);
  G4Element* O = G4NistManager::Instance()->FindOrBuildElement("O");
  liquidO2->AddElement(O, 2);  // O2 molecules

  // Liquid oxygen optical properties
  G4MaterialPropertiesTable* o2MPT = new G4MaterialPropertiesTable();

  // Photon energies (wavelengths from 200-700 nm)
  const G4int nEntries = 10;
  G4double photonEnergy[nEntries] = {
    1.77*eV, 2.07*eV, 2.48*eV, 2.76*eV, 3.10*eV,
    3.54*eV, 4.13*eV, 4.96*eV, 5.64*eV, 6.20*eV
  };

  // Refractive index of liquid oxygen (~1.22)
  G4double refractiveIndex[nEntries] = {
    1.220, 1.220, 1.221, 1.221, 1.222,
    1.222, 1.223, 1.224, 1.225, 1.226
  };

  // Absorption length (transparent, ~5m)
  G4double absorption[nEntries] = {
    5.*m, 5.*m, 5.*m, 5.*m, 5.*m,
    5.*m, 5.*m, 5.*m, 5.*m, 5.*m
  };

  o2MPT->AddProperty("RINDEX", photonEnergy, refractiveIndex, nEntries);
  o2MPT->AddProperty("ABSLENGTH", photonEnergy, absorption, nEntries);

  liquidO2->SetMaterialPropertiesTable(o2MPT);

  return liquidO2;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

G4VPhysicalVolume* DetectorConstruction::Construct()
{
  G4NistManager* nist = G4NistManager::Instance();
  
  // Option to switch on/off checking of volumes overlaps
  G4bool checkOverlaps = true;

  //
  // World
  //
  G4double world_size = 1.2 * std::max({fDetectorSizeX, fDetectorSizeY, fDetectorSizeZ});
  G4Material* world_mat = nist->FindOrBuildMaterial("G4_AIR");

  auto solidWorld = new G4Box("World", 
                              0.5 * world_size, 
                              0.5 * world_size, 
                              0.5 * world_size);

  auto logicWorld = new G4LogicalVolume(solidWorld,
                                        world_mat,
                                        "World");

  auto physWorld = new G4PVPlacement(nullptr,
                                     G4ThreeVector(),
                                     logicWorld,
                                     "World",
                                     nullptr,
                                     false,
                                     0,
                                     checkOverlaps);

  //
  // Detector Volume - Monolithic
  //
  G4Material* detector_mat = nullptr;
  if (fDetectorMaterialName == "Water") {
    detector_mat = fWater;
  } else if (fDetectorMaterialName == "LiquidArgon") {
    detector_mat = fLiquidArgon;
  } else if (fDetectorMaterialName == "Ice") {
    detector_mat = fIce;
  } else if (fDetectorMaterialName == "LiquidScintillator") {
    detector_mat = fLiquidScintillator;
  } else if (fDetectorMaterialName == "LiquidHydrogen") {
    detector_mat = fLiquidHydrogen;
  } else if (fDetectorMaterialName == "LiquidOxygen") {
    detector_mat = fLiquidOxygen;
  } else {
    detector_mat = fWater; // Default to water
  }

  auto solidDetector = new G4Box("Detector",
                                 0.5 * fDetectorSizeX,
                                 0.5 * fDetectorSizeY,
                                 0.5 * fDetectorSizeZ);

  fDetectorLogical = new G4LogicalVolume(solidDetector,
                                         detector_mat,
                                         "DetectorLogical");

  new G4PVPlacement(nullptr,
                    G4ThreeVector(),
                    fDetectorLogical,
                    "Detector",
                    logicWorld,
                    false,
                    0,
                    checkOverlaps);

  return physWorld;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DetectorConstruction::ConstructSDandField()
{
  // No sensitive detectors or fields for now
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DetectorConstruction::SetDetectorSize(G4double x, G4double y, G4double z)
{
  fDetectorSizeX = x;
  fDetectorSizeY = y;
  fDetectorSizeZ = z;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void DetectorConstruction::SetDetectorMaterial(const G4String& materialName)
{
  fDetectorMaterialName = materialName;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim