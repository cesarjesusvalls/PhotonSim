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
/// \file PhotonSim/src/SteppingAction.cc
/// \brief Implementation of the PhotonSim::SteppingAction class

#include "SteppingAction.hh"
#include "DetectorConstruction.hh"
#include "EventAction.hh"
#include "DataManager.hh"

#include "G4Event.hh"
#include "G4LogicalVolume.hh"
#include "G4RunManager.hh"
#include "G4Step.hh"
#include "G4Track.hh"
#include "G4ParticleDefinition.hh"
#include "G4OpticalPhoton.hh"
#include "G4VProcess.hh"
#include "G4SystemOfUnits.hh"
#include "G4PhysicalConstants.hh"
#include "G4DynamicParticle.hh"
#include "G4SteppingManager.hh"

namespace PhotonSim
{

// Simple dummy process class for custom process names (deflection handling)
class DummyProcess : public G4VProcess {
public:
  DummyProcess(const G4String& name) : G4VProcess(name, fUserDefined) {}
  virtual ~DummyProcess() {}

  // Minimal required overrides (never actually called)
  virtual G4double PostStepGetPhysicalInteractionLength(
    const G4Track&, G4double, G4ForceCondition*) { return DBL_MAX; }
  virtual G4VParticleChange* PostStepDoIt(const G4Track&, const G4Step&) { return nullptr; }
  virtual G4double AlongStepGetPhysicalInteractionLength(
    const G4Track&, G4double, G4double, G4double&, G4GPILSelection*) { return DBL_MAX; }
  virtual G4VParticleChange* AlongStepDoIt(const G4Track&, const G4Step&) { return nullptr; }
  virtual G4double AtRestGetPhysicalInteractionLength(
    const G4Track&, G4ForceCondition*) { return DBL_MAX; }
  virtual G4VParticleChange* AtRestDoIt(const G4Track&, const G4Step&) { return nullptr; }
};

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

SteppingAction::SteppingAction(EventAction* eventAction) : fEventAction(eventAction) {}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void SteppingAction::UserSteppingAction(const G4Step* step)
{
  // Get the track and particle information
  G4Track* track = step->GetTrack();
  G4ParticleDefinition* particle = track->GetDefinition();

  DataManager* dataManager = DataManager::GetInstance();

  // Register all new non-optical-photon tracks (first step) with full
  // information. Optical photons are recorded separately via
  // AddOpticalPhoton; registering them as TrackInfo rows would add
  // O(million) duplicate entries per event (their kinematics already
  // live on OpticalPhotonsRaw).
  if (track->GetCurrentStepNumber() == 1 &&
      particle != G4OpticalPhoton::OpticalPhotonDefinition()) {
    G4int trackID = track->GetTrackID();
    G4String particleName = particle->GetParticleName();
    G4int parentID = track->GetParentID();
    G4ThreeVector position = track->GetVertexPosition();
    // Use vertex momentum for initial track info (more reliable for particles created mid-step)
    G4ThreeVector momentum = track->GetVertexMomentumDirection() * track->GetVertexKineticEnergy();
    G4double energy = track->GetVertexKineticEnergy();
    G4double time = track->GetGlobalTime() - step->GetDeltaTime();
    G4int pdgCode = particle->GetPDGEncoding();

    // Kill particles created after 10 microseconds (nuclear de-excitations, long-lived decays)
    // These are physically correct but irrelevant for neutrino physics and contaminate timing
    if (time > 10000.0 * ns) {
      track->SetTrackStatus(fStopAndKill);
      return;  // Don't register or process this track
    }

    const G4VProcess* creationProcess = track->GetCreatorProcess();
    G4String processName = creationProcess ? creationProcess->GetProcessName() : "Primary";

    dataManager->RegisterTrack(trackID, particleName, parentID, position, momentum, energy, time, pdgCode, processName);
  }

  // Deflection detection: kill and replace pions that deflect significantly.
  // Handles hadronic elastic scattering (hadElastic) and hadronic ionization
  // (hIoni). Inelastic processes always kill tracks, so they don't reach
  // here. The track-level split is what gives LUCiD's Python categorizer a
  // clean signal — post-deflection segments belong to a separate track id
  // with creator process "Deflection_*". ONLY check deflections for
  // continuing tracks (step > 1), not newly created tracks.
  G4String particleName = particle->GetParticleName();
  if ((particleName == "pi+" || particleName == "pi-") && track->GetCurrentStepNumber() > 1) {
    G4int trackID = track->GetTrackID();
    TrackInfo* info = dataManager->GetTrackInfo(trackID);

    if (info) {
      const G4VProcess* process = step->GetPostStepPoint()->GetProcessDefinedStep();
      if (process) {
        G4String currentProcessName = process->GetProcessName();

        // Calculate angle change and track status
        G4ThreeVector postMomentum = track->GetMomentumDirection();
        G4double angle = std::acos(info->preMomentumDir.dot(postMomentum));
        G4TrackStatus status = track->GetTrackStatus();

        // Only skip deflection handling for tracks being killed.
        // Suspended tracks (fSuspend) should still be handled — they're
        // temporarily paused. A bare `return` here would also skip the
        // segment-recording block below, so the stopping pion's final
        // step would be absent from Segment_NCherenkov while its
        // Cerenkov secondaries still bumped the count on their first
        // step.
        if (status != fStopAndKill &&
            (currentProcessName == "hadElastic" || currentProcessName == "hIoni")) {

          // If deflection > 5 degrees, kill and replace the track
          if (angle > 5.0 * deg) {
            // Use stored position and time where old momentum was recorded —
            // the TRUE kink point.
            G4ThreeVector kinkPosition = info->preMomentumPos;
            G4double kinkTime = info->preMomentumTime;
            G4ThreeVector postStepMomentum = track->GetMomentum();  // Deflected momentum
            G4int oldTrackID = track->GetTrackID();
            G4TrackStatus originalStatus = status;

            // Kill current track
            track->SetTrackStatus(fStopAndKill);

            // Spawn replacement at the kink point with deflected momentum.
            G4DynamicParticle* dynParticle = new G4DynamicParticle(
              particle,
              postStepMomentum
            );
            G4Track* secondary = new G4Track(
              dynParticle,
              kinkTime,
              kinkPosition
            );
            secondary->SetParentID(oldTrackID);
            secondary->SetTrackStatus(originalStatus);

            // Tag with a custom creator process so LUCiD's Python
            // categorizer recognises deflection-spawned pions.
            G4String deflectionProcessName = "Deflection_" + currentProcessName;
            G4VProcess* deflectionProcess = new DummyProcess(deflectionProcessName);
            secondary->SetCreatorProcess(deflectionProcess);

            fpSteppingManager->GetfSecondary()->push_back(secondary);
          }
        }
      }

      // Update momentum, position, and time as a synchronized triplet for
      // the next deflection check. Store post-step values (where the track
      // is NOW after this step completes).
      dataManager->UpdatePionMomentum(trackID,
                                     track->GetMomentumDirection(),
                                     track->GetPosition(),
                                     track->GetGlobalTime());
    }
  }

  // Optical photons: record on first step (creation) only.
  if (particle == G4OpticalPhoton::OpticalPhotonDefinition()) {
    if (track->GetCurrentStepNumber() == 1) {
      // Get the creation process from the track
      const G4VProcess* creationProcess = track->GetCreatorProcess();
      G4String processName = "Unknown";
      if (creationProcess) {
        processName = creationProcess->GetProcessName();
      }

      G4int parentID = track->GetParentID();

      // Get position and direction at creation
      G4ThreeVector position = track->GetVertexPosition();
      G4ThreeVector direction = track->GetVertexMomentumDirection();
      G4double time = track->GetGlobalTime() - step->GetDeltaTime();

      // Get polarization vector
      G4ThreeVector polarization = track->GetPolarization();

      // Calculate wavelength from photon energy
      G4double photonEnergy = track->GetKineticEnergy();
      G4double wavelength = (h_Planck * c_light) / photonEnergy;

      // Record this optical photon. parentID is the immediate Geant4
      // parent track that emitted the photon — used post-merge in
      // EndEvent to look up the originating segment via
      // Photon_SegmentIndex.
      dataManager->AddOpticalPhoton(position.x(), position.y(), position.z(),
                                   direction.x(), direction.y(), direction.z(),
                                   time, wavelength,
                                   polarization.x(), polarization.y(), polarization.z(),
                                   processName,
                                   parentID);

      // If this is a Cerenkov photon, increment the count for the parent track
      if (processName == "Cerenkov") {
        dataManager->IncrementCherenkovCount(parentID);
      }
    }
    return; // Don't process further for optical photons
  }

  // Also collect energy deposition in the detector volume for general tracking
  if (!fDetectorVolume) {
    const auto detConstruction = static_cast<const DetectorConstruction*>(
      G4RunManager::GetRunManager()->GetUserDetectorConstruction());
    fDetectorVolume = detConstruction->GetDetectorVolume();
  }

  // Get volume of the current step
  G4LogicalVolume* volume =
    step->GetPreStepPoint()->GetTouchableHandle()->GetVolume()->GetLogicalVolume();

  // Check if we are in detector volume and collect energy deposition
  if (volume == fDetectorVolume) {
    G4double edepStep = step->GetTotalEnergyDeposit();
    fEventAction->AddEdep(edepStep);

    // Drive the dE/dx histogram. Per-step Edep_* ROOT branches are gone;
    // LUCiD reads the histogram alone via build_dedx_table.py.
    if (edepStep > 0.0) {
      G4ThreeVector stepPos = step->GetPostStepPoint()->GetPosition();
      G4double stepLength = step->GetStepLength();
      G4String edepParticleName = particle->GetParticleName();

      dataManager->AddEnergyDeposit(stepPos.x(), stepPos.y(), stepPos.z(),
                                   edepStep, stepLength, edepParticleName);
    }
  }

  // Record track segment for all non-optical photon tracks. Every
  // track's steps land in fAllTrackSegments; LUCiD derives the
  // meaningful subset via groupby on Segment_TrackID +
  // Segment_NCherenkov.
  // Only collect when individual photon storage is enabled (needed for per-particle data)
  if (dataManager->GetStoreIndividualPhotons()) {
    G4int trackID = track->GetTrackID();
    G4int parentID = track->GetParentID();
    G4int pdgCode = particle->GetPDGEncoding();
    G4String segParticleName = particle->GetParticleName();
    G4double initialEnergy = track->GetVertexKineticEnergy();

    // Get step positions and direction
    G4ThreeVector prePos = step->GetPreStepPoint()->GetPosition();
    G4ThreeVector postPos = step->GetPostStepPoint()->GetPosition();
    G4ThreeVector preDir = step->GetPreStepPoint()->GetMomentumDirection();
    G4double edep = step->GetTotalEnergyDeposit();
    G4double preTime = step->GetPreStepPoint()->GetGlobalTime();

    // β = v/c at pre-step (drives Cherenkov physics)
    G4double betaStart = step->GetPreStepPoint()->GetBeta();

    // Count Cherenkov photons emitted in this step. G4 emits them as secondaries
    // with creator process "Cerenkov" — count those produced by this step only.
    G4int nCherenkovInStep = 0;
    const std::vector<const G4Track*>* secondaries = step->GetSecondaryInCurrentStep();
    if (secondaries) {
      for (const G4Track* sec : *secondaries) {
        const G4VProcess* creator = sec->GetCreatorProcess();
        if (creator && creator->GetProcessName() == "Cerenkov") {
          ++nCherenkovInStep;
        }
      }
    }

    dataManager->AddTrackSegment(trackID, parentID, pdgCode,
                                segParticleName, initialEnergy,
                                prePos.x(), prePos.y(), prePos.z(),
                                postPos.x(), postPos.y(), postPos.z(),
                                preDir.x(), preDir.y(), preDir.z(),
                                edep, preTime,
                                betaStart, nCherenkovInStep);
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim
