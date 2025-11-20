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

  // Debug flag - can be enabled via environment variable
  static G4bool debugPions = std::getenv("DEBUG_PIONS") != nullptr;
  static G4bool debugGammas = std::getenv("DEBUG_GAMMAS") != nullptr;
  static G4bool debugMuons = std::getenv("DEBUG_MUONS") != nullptr;

  // Register all new tracks (first step) with full information
  if (track->GetCurrentStepNumber() == 1) {
    G4int trackID = track->GetTrackID();
    G4String particleName = particle->GetParticleName();
    G4int parentID = track->GetParentID();
    G4ThreeVector position = track->GetVertexPosition();
    // Use vertex momentum for initial track info (more reliable for particles created mid-step)
    G4ThreeVector momentum = track->GetVertexMomentumDirection() * track->GetVertexKineticEnergy();
    G4double energy = track->GetVertexKineticEnergy();
    G4double time = track->GetGlobalTime() - step->GetDeltaTime();
    G4int pdgCode = particle->GetPDGEncoding();

    dataManager->RegisterTrack(trackID, particleName, parentID, position, momentum, energy, time, pdgCode);

    // Category classification logic
    const G4VProcess* creationProcess = track->GetCreatorProcess();
    G4String processName = creationProcess ? creationProcess->GetProcessName() : "Primary";

    // DEBUG: Print all new pion creations
    if (debugPions && (particleName == "pi+" || particleName == "pi-")) {
      G4cout << "\n=== NEW PION CREATED ===" << G4endl;
      G4cout << "  TrackID: " << trackID << G4endl;
      G4cout << "  Particle: " << particleName << " (PDG: " << pdgCode << ")" << G4endl;
      G4cout << "  ParentID: " << parentID << G4endl;
      TrackInfo* parentInfo = dataManager->GetTrackInfo(parentID);
      if (parentInfo) {
        G4cout << "  Parent particle: " << parentInfo->particleName
               << " (PDG: " << parentInfo->pdgCode << ")" << G4endl;
        G4cout << "  Parent category: " << parentInfo->category << G4endl;
      }
      G4cout << "  Creation process: " << processName << G4endl;
      G4cout << "  Energy: " << energy/MeV << " MeV" << G4endl;
      G4cout << "  Position: (" << position.x()/cm << ", " << position.y()/cm
             << ", " << position.z()/cm << ") cm" << G4endl;
    }

    // DEBUG: Print gamma creation from pi0 decay
    if (debugGammas && particleName == "gamma" && processName == "Decay") {
      TrackInfo* parentInfo = dataManager->GetTrackInfo(parentID);
      if (parentInfo && parentInfo->particleName == "pi0") {
        G4cout << "\n=== GAMMA FROM PI0 DECAY ===" << G4endl;
        G4cout << "  TrackID: " << trackID << G4endl;
        G4cout << "  ParentID: " << parentID << " (pi0)" << G4endl;
        G4cout << "  Energy: " << energy/MeV << " MeV" << G4endl;
        G4cout << "  Momentum: (" << momentum.x()/MeV << ", " << momentum.y()/MeV
               << ", " << momentum.z()/MeV << ") MeV" << G4endl;
        G4cout << "  Momentum magnitude: " << momentum.mag()/MeV << " MeV" << G4endl;
        G4cout << "  Unit direction: (" << momentum.unit().x() << ", " << momentum.unit().y()
               << ", " << momentum.unit().z() << ")" << G4endl;
        G4cout << "  Position: (" << position.x()/cm << ", " << position.y()/cm
               << ", " << position.z()/cm << ") cm" << G4endl;
      }
    }

    // DEBUG: Print all muon creations
    if (debugMuons && (particleName == "mu-" || particleName == "mu+")) {
      G4cout << "\n=== NEW MUON CREATED ===" << G4endl;
      G4cout << "  TrackID: " << trackID << G4endl;
      G4cout << "  Particle: " << particleName << " (PDG: " << pdgCode << ")" << G4endl;
      G4cout << "  ParentID: " << parentID << G4endl;
      TrackInfo* parentInfo = dataManager->GetTrackInfo(parentID);
      if (parentInfo) {
        G4cout << "  Parent particle: " << parentInfo->particleName
               << " (PDG: " << parentInfo->pdgCode << ")" << G4endl;
        G4cout << "  Parent category: " << parentInfo->category << G4endl;
      }
      G4cout << "  Creation process: " << processName << G4endl;
      G4cout << "  Energy: " << energy/MeV << " MeV" << G4endl;
      G4cout << "  Position: (" << position.x()/cm << ", " << position.y()/cm
             << ", " << position.z()/cm << ") cm" << G4endl;
    }

    // 1. Primary particles (parentID == 0)
    if (parentID == 0) {
      G4int subID = dataManager->GetNextPrimaryID();
      dataManager->UpdateTrackCategory(trackID, kPrimary, subID, 0);

      if (debugPions && (particleName == "pi+" || particleName == "pi-")) {
        G4cout << "  >>> CLASSIFIED as PRIMARY (subID=" << subID << ")" << G4endl;
      }
    }

    // 2. Decay electrons: electrons from Decay or muMinusCaptureAtRest process
    else if (particleName == "e-" || particleName == "e+") {
      // Accept electrons from both free decay and bound muon decay
      // - "Decay": free muon/pion decay
      // - "muMinusCaptureAtRest": bound muon decay (~80-90% branch) or nuclear capture (10-20% - no electron)
      if (processName == "Decay" || processName == "muMinusCaptureAtRest") {
        // Check DIRECT parent is muon or pion
        TrackInfo* parentInfo = dataManager->GetTrackInfo(parentID);
        if (parentInfo && (parentInfo->particleName == "mu-" || parentInfo->particleName == "mu+" ||
                           parentInfo->particleName == "pi-" || parentInfo->particleName == "pi+")) {
          // Apply energy threshold to exclude Auger electrons from muonic atom de-excitation
          // and other low-energy secondaries (typically eV-keV range)
          if (energy > 1.0 * MeV) {
            // Assign new decay electron SubID using DIRECT parent
            G4int subID = dataManager->GetNextDecayElectronID();
            dataManager->UpdateTrackCategory(trackID, kDecayElectron, subID, parentID);
          }
        }
      }
    }

    // 3. Gamma showers: gammas from pi0 decay
    else if (particleName == "gamma") {
      if (processName == "Decay") {
        TrackInfo* parentInfo = dataManager->GetTrackInfo(parentID);
        if (parentInfo && parentInfo->particleName == "pi0") {
          // Assign new gamma shower SubID
          G4int subID = dataManager->GetNextGammaShowerID();
          dataManager->UpdateTrackCategory(trackID, kGammaShower, subID, parentID);
        }
      }
    }

    // 4. Secondary pions: charged pions from hadronic inelastic interactions or deflections
    else if (particleName == "pi+" || particleName == "pi-") {
      TrackInfo* parentInfo = dataManager->GetTrackInfo(parentID);

      // Check if created from inelastic hadronic process, deflection handling,
      // OR if parent is a categorized pion (deflection-created case where SetCreatorProcess fails)
      G4bool isFromInelastic = processName.contains("Inelastic") || processName.contains("inelastic");
      G4bool isFromDeflection = processName.contains("Deflection");
      G4bool isFromCategorizedPion = (parentInfo &&
                                      (parentInfo->particleName == "pi+" || parentInfo->particleName == "pi-") &&
                                      parentInfo->category >= 0);

      if (isFromInelastic || isFromDeflection || isFromCategorizedPion) {
        // TEMPORARY: Threshold set to 0 for debugging (TODO: restore to 250 MeV/c)
        // Skip classification for low-momentum secondary pions (<250 MeV/c)
        // They don't produce Cherenkov photons, so their photons should use parent's genealogy
        G4double pionMomentum = track->GetMomentum().mag();
        if (pionMomentum >= 160 * MeV) {  // TEMPORARY: was 250 * MeV
          // Only classify pions above Cherenkov threshold

          // Find the category-relevant parent
          G4int categoryParent = parentID;
          while (parentInfo && parentInfo->category < 0 && parentInfo->parentTrackID > 0) {
            categoryParent = parentInfo->parentTrackID;
            parentInfo = dataManager->GetTrackInfo(categoryParent);
          }

          G4int subID = dataManager->GetNextSecondaryPionID();
          dataManager->UpdateTrackCategory(trackID, kSecondaryPion, subID, categoryParent);

          if (debugPions) {
            G4cout << "  >>> CLASSIFIED as SECONDARY PION (subID=" << subID << ")" << G4endl;
            G4cout << "      Creation process: " << processName << G4endl;
            if (isFromCategorizedPion) {
              G4cout << "      Reason: Parent is categorized pion (deflection-created)" << G4endl;
            }
            G4cout << "      Category parent: " << categoryParent << G4endl;
          }

          // DISABLED: Check if parent needs photon relabeling (deflection case)
          // parentInfo = dataManager->GetTrackInfo(parentID);
          // if (parentInfo && parentInfo->needsPhotonRelabeling) {
          //   // Relabel photons from the parent that were created during/after deflection
          //   dataManager->RelabelPhotonsForDeflection(trackID, parentID, parentInfo->relabelingTime);

          //   if (debugPions) {
          //     G4cout << "      >>> PHOTON RELABELING: Reassigning photons from parent " << parentID
          //                << " created after time " << parentInfo->relabelingTime/ns << " ns" << G4endl;
          //   }

          //   // Clear the flag to prevent duplicate relabeling
          //   parentInfo->needsPhotonRelabeling = false;
          // }
        }
        // else: pion below Cherenkov threshold - skip classification
      } else if (debugPions) {
        G4cout << "  >>> NOT classified as secondary (process: " << processName << ")" << G4endl;
      }
    }
  }

  // 5. Deflection detection: kill and replace pions that deflect significantly
  // Handles: hadronic elastic scattering (hadElastic), hadronic ionization (hIoni)
  // Inelastic processes always kill tracks, so we don't need to handle them here
  // This handles cases where GEANT4 continues the track instead of killing it
  // ONLY check deflections for continuing tracks (step > 1), not newly created tracks
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
        G4double angleDeg = angle / deg;
        G4TrackStatus status = track->GetTrackStatus();

        // Only skip deflection handling for tracks being killed
        // Suspended tracks (fSuspend) should still be handled - they're temporarily paused
        if (status == fStopAndKill) {
          return; // Skip deflection handling for killed tracks
        }

        // Check for processes that cause significant deflections: hadElastic, hIoni
        // (Inelastic processes always kill tracks, so they never reach here)
        if (currentProcessName == "hadElastic" || currentProcessName == "hIoni") {

          // If deflection > 5 degrees, kill and replace the track
          if (angle > 5.0 * deg) {
            if (debugPions) {
              G4cout << "\n--- PION DEFLECTION PROCESS (>5° - Handling) ---" << G4endl;
              G4cout << "  TrackID: " << trackID << G4endl;
              G4cout << "  Particle: " << particleName << G4endl;
              G4cout << "  Process: " << currentProcessName << G4endl;
              G4cout << "  Deflection angle: " << angleDeg << " degrees" << G4endl;
              G4cout << "  Current category: " << info->category << G4endl;
              G4cout << "  Track status: " << track->GetTrackStatus() << G4endl;
              G4cout << "  >>> DEFLECTION >5°: Killing track and creating new secondary" << G4endl;
            }

            // Use stored position and time where old momentum was recorded
            // This is the TRUE kink point - where the particle had the old momentum
            G4ThreeVector kinkPosition = info->preMomentumPos;
            G4double kinkTime = info->preMomentumTime;
            G4ThreeVector postStepMomentum = track->GetMomentum();  // Deflected momentum
            G4double postStepEnergy = track->GetKineticEnergy();
            G4int oldTrackID = track->GetTrackID();

            // Save original track status to apply to new track
            G4TrackStatus originalStatus = status;

            // Kill current track
            track->SetTrackStatus(fStopAndKill);

            // Create new dynamic particle with deflected (post-step) momentum
            G4DynamicParticle* dynParticle = new G4DynamicParticle(
              particle,
              postStepMomentum
            );

            // Create new track at the exact kink point
            // kinkPosition and kinkTime are where the old momentum (preMomentumDir) was recorded
            G4Track* secondary = new G4Track(
              dynParticle,
              kinkTime,
              kinkPosition
            );
            secondary->SetParentID(oldTrackID);

            // Set new track to have the same status as the original track
            // (fAlive stays fAlive, fSuspend stays fSuspend)
            secondary->SetTrackStatus(originalStatus);

            // Set custom creator process name to identify deflection-created pions
            G4String deflectionProcessName = "Deflection_" + currentProcessName;
            G4VProcess* deflectionProcess = new DummyProcess(deflectionProcessName);
            secondary->SetCreatorProcess(deflectionProcess);

            // Store relabeling information for the new track
            // We'll use this in the first step to reassign photons from the deflection step
            // Note: We store this now, but the new track won't be registered until its first step
            // So we'll need to retrieve this info when the track is registered

            // Add to secondary stack
            fpSteppingManager->GetfSecondary()->push_back(secondary);

            // Store the relabeling info for when the new track gets registered
            // We'll mark it in the track info during registration (step 1)
            dataManager->GetTrackInfo(oldTrackID)->needsPhotonRelabeling = true;
            dataManager->GetTrackInfo(oldTrackID)->relabelingTime = kinkTime;

            if (debugPions) {
              G4cout << "      Old track ID: " << oldTrackID << " (killed)" << G4endl;
              G4cout << "      New secondary will be created with parent ID: " << oldTrackID << G4endl;
              G4cout << "      Energy: " << postStepEnergy/MeV << " MeV" << G4endl;
              G4cout << "      Kink position: (" << kinkPosition.x()/cm << ", " << kinkPosition.y()/cm
                     << ", " << kinkPosition.z()/cm << ") cm" << G4endl;
              G4cout << "      Deflection will trigger photon relabeling at time: " << kinkTime/ns << " ns" << G4endl;
            }
          }
          // Note: We don't print for deflections <5° as they're too frequent (especially hIoni)
        }
      }

      // Update momentum, position, and time as synchronized triplet for next deflection check
      // Store post-step values (where the track is NOW after this step completes)
      dataManager->UpdatePionMomentum(trackID,
                                     track->GetMomentumDirection(),
                                     track->GetPosition(),
                                     track->GetGlobalTime());
    }
  }

  // Check if this is an optical photon on its first step (creation)
  if (particle == G4OpticalPhoton::OpticalPhotonDefinition()) {
    // Only record optical photons at their first step (when they're created)
    if (track->GetCurrentStepNumber() == 1) {

      // Get the creation process from the track
      const G4VProcess* creationProcess = track->GetCreatorProcess();
      G4String processName = "Unknown";
      if (creationProcess) {
        processName = creationProcess->GetProcessName();
      }

      // Find category-relevant parent by tracing back through ancestry
      G4int parentID = track->GetParentID();
      G4int categoryParentID = parentID;
      TrackInfo* parentInfo = dataManager->GetTrackInfo(parentID);

      // Trace back to find most recent categorized ancestor
      while (parentInfo && parentInfo->category < 0 && parentInfo->parentTrackID > 0) {
        categoryParentID = parentInfo->parentTrackID;
        parentInfo = dataManager->GetTrackInfo(categoryParentID);
      }

      // Build genealogy using the DataManager method
      std::vector<G4int> genealogy = dataManager->BuildGenealogy(categoryParentID);

      // Get position and direction at creation
      G4ThreeVector position = track->GetVertexPosition();
      G4ThreeVector direction = track->GetVertexMomentumDirection();
      G4double time = track->GetGlobalTime() - step->GetDeltaTime();

      // Calculate wavelength from photon energy
      G4double photonEnergy = track->GetKineticEnergy();
      G4double wavelength = (h_Planck * c_light) / photonEnergy;

      // Record this optical photon with genealogy
      dataManager->AddOpticalPhoton(position.x(), position.y(), position.z(),
                                   direction.x(), direction.y(), direction.z(),
                                   time, wavelength, processName,
                                   genealogy);
    }
    return; // Don't process further for optical photons
  }
  
  // Debug prints removed
  
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
    
    // Store detailed energy deposit information for scintillation analysis
    if (edepStep > 0.0) {
      G4ThreeVector stepPos = step->GetPostStepPoint()->GetPosition();
      G4double stepTime = step->GetPostStepPoint()->GetGlobalTime();
      G4String particleName = particle->GetParticleName();
      G4int trackID = track->GetTrackID();
      G4int parentID = track->GetParentID();
      
      dataManager->AddEnergyDeposit(stepPos.x(), stepPos.y(), stepPos.z(),
                                   edepStep, stepTime, particleName,
                                   trackID, parentID);
      
      // Debug prints removed
    }
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim