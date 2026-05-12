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
#include <memory>
#include <string>
#include <vector>

class G4ParticleGun;
class G4Event;

namespace PhotonSim
{

class PrimaryGeneratorMessenger;
class RooTrackerReader;

/// Specification for an individual primary particle
struct PrimaryParticleSpec {
  G4String particleName;
  G4double energy;           // Fixed energy (used when useRandomEnergy is false)
  G4double minEnergy = 0.0;  // Minimum energy for random sampling
  G4double maxEnergy = 0.0;  // Maximum energy for random sampling
  G4bool useRandomEnergy = false;  // If true, sample uniformly from [minEnergy, maxEnergy]
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
    void AddPrimaryWithEnergyRange(const G4String& particleName, G4double minEnergy, G4double maxEnergy);
    void ClearPrimaries() { fPrimaryList.clear(); }

    // Bomb mode: per event, fire N=Uniform[fBombMin,fBombMax] particles drawn
    // with replacement from fBombPool, each with energy uniform in its
    // candidate range and an isotropic direction.
    void AddBombCandidate(const G4String& particleName, G4double minEnergy, G4double maxEnergy);
    void ClearBombCandidates() { fBombPool.clear(); }
    void SetBombMin(G4int n) { fBombMin = n; }
    void SetBombMax(G4int n) { fBombMax = n; }
    void SetBombMode(G4bool on) { fBombMode = on; }

    // GENIE rooTracker input: when set, PhotonSim injects final-state
    // particles from each rootracker entry as per-event primaries.
    void SetGenieInput(const G4String& path);
    void SetGenieIsotropic(G4bool iso) { fGenieIsotropic = iso; }
    G4bool HasGenieInput() const;

    // method to access particle gun
    const G4ParticleGun* GetParticleGun() const { return fParticleGun; }
    G4double GetTrueEnergy() const { return fTrueEnergy; }
    G4double GetMinEnergy() const { return fMinEnergy; }
    G4double GetMaxEnergy() const { return fMaxEnergy; }
    G4bool GetRandomEnergy() const { return fRandomEnergy; }
    G4bool GetRandomDirection() const { return fRandomDirection; }
    G4int GetNumberOfPrimaries() const { return fNumberOfPrimaries; }

    // GENIE per-event metadata (set when the current G4 event was fired from
    // a GENIE rootracker entry; cleared otherwise). EventAction forwards
    // these into DataManager so the labl output can surface neutrino probe
    // info per v5 interaction row.
    G4int    GetCurrentGenieEntryID() const { return fGenieCurrentEventEntry; }
    G4int    GetCurrentGenieNuPdg() const   { return fGenieCurrentEventNuPdg; }
    G4double GetCurrentGenieNuKE() const    { return fGenieCurrentEventNuKE; }

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

    // Bomb-mode candidate pool + per-event multiplicity bounds.
    std::vector<PrimaryParticleSpec> fBombPool;
    G4int fBombMin = 1;
    G4int fBombMax = 5;
    G4bool fBombMode = false;

    // GENIE rooTracker primary source (optional). One rootracker entry maps
    // to one G4 event; all status==1 final-state particles from that entry
    // are fired together, mirroring the particle-gun heterogeneous list.
    // Per-entry random rotation is applied once so relative FSI kinematics
    // are preserved.
    std::unique_ptr<RooTrackerReader> fGenieReader;
    G4bool fGenieIsotropic = true;
    long long fGenieCurrentEntry = -1;   // last rootracker entry loaded
    G4double fGenieRotAxisX = 0.0, fGenieRotAxisY = 0.0, fGenieRotAxisZ = 1.0;
    G4double fGenieRotAngle = 0.0;

    // Per-event cache of the GENIE-level provenance (rootracker entry index
    // + incoming neutrino kinematics) so EventAction can read them back
    // after GeneratePrimaries fires. -1 / 0 / NaN for non-GENIE events.
    G4int    fGenieCurrentEventEntry = -1;
    G4int    fGenieCurrentEventNuPdg = 0;
    G4double fGenieCurrentEventNuKE = 0.0;
};

}  // namespace PhotonSim

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

#endif
