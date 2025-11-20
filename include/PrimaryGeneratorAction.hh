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
/// \file PhotonSim/include/PrimaryGeneratorAction.hh
/// \brief Definition of the PhotonSim::PrimaryGeneratorAction class

#ifndef PhotonSimPrimaryGeneratorAction_h
#define PhotonSimPrimaryGeneratorAction_h 1

#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4String.hh"
#include "G4SystemOfUnits.hh"
#include "G4ThreeVector.hh"
#include <vector>

class G4ParticleGun;
class G4Event;

namespace PhotonSim
{

class PrimaryGeneratorMessenger;

/// Specification for an individual primary particle
struct PrimaryParticleSpec {
  G4String particleName;
  G4double energy;
};

/// The primary generator action class with configurable particle gun.
/// Generates particles at the center of the detector (0,0,0) with 
/// direction along (0,0,1) and configurable energy and particle type.

class PrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction
{
  public:
    PrimaryGeneratorAction();
    ~PrimaryGeneratorAction() override;

    // method from the base class
    void GeneratePrimaries(G4Event*) override;

    // methods to configure the particle gun
    void SetParticleType(const G4String& particleName);
    void SetParticleEnergy(G4double energy);
    void SetEnergyRange(G4double minEnergy, G4double maxEnergy);
    void SetRandomEnergy(G4bool useRandom) { fRandomEnergy = useRandom; }
    void SetParticlePosition(const G4ThreeVector& position);
    void SetParticleDirection(const G4ThreeVector& direction);
    void SetRandomDirection(G4bool useRandom) { fRandomDirection = useRandom; }
    void SetNumberOfPrimaries(G4int n) { fNumberOfPrimaries = n; }

    // methods for heterogeneous primary particle list
    void AddPrimary(const G4String& particleName, G4double energy);
    void ClearPrimaries() { fPrimaryList.clear(); }

    // method to access particle gun
    const G4ParticleGun* GetParticleGun() const { return fParticleGun; }
    G4double GetTrueEnergy() const { return fTrueEnergy; }
    G4double GetMinEnergy() const { return fMinEnergy; }
    G4double GetMaxEnergy() const { return fMaxEnergy; }
    G4bool GetRandomEnergy() const { return fRandomEnergy; }
    G4bool GetRandomDirection() const { return fRandomDirection; }
    G4int GetNumberOfPrimaries() const { return fNumberOfPrimaries; }

  private:
    G4ParticleGun* fParticleGun = nullptr;
    PrimaryGeneratorMessenger* fMessenger = nullptr;

    // Configurable parameters
    G4double fMinEnergy = 100.0*MeV;
    G4double fMaxEnergy = 500.0*MeV;
    G4bool fRandomEnergy = false;
    G4bool fRandomDirection = false;
    G4double fTrueEnergy = 0.0; // Store the actual energy used for this event
    G4int fNumberOfPrimaries = 1; // Number of primary particles per event

    // List of heterogeneous primary particles
    std::vector<PrimaryParticleSpec> fPrimaryList;
};

}  // namespace PhotonSim

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#endif
