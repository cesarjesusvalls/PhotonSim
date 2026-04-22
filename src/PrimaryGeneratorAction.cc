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
/// \file PhotonSim/src/PrimaryGeneratorAction.cc
/// \brief Implementation of the PhotonSim::PrimaryGeneratorAction class

#include "PrimaryGeneratorAction.hh"
#include "PrimaryGeneratorMessenger.hh"
#include "RooTrackerReader.hh"

#include "G4Event.hh"
#include "G4ParticleGun.hh"
#include "G4ParticleTable.hh"
#include "G4ParticleDefinition.hh"
#include "G4PrimaryParticle.hh"
#include "G4PrimaryVertex.hh"
#include "G4RotationMatrix.hh"
#include "G4SystemOfUnits.hh"
#include "Randomize.hh"

#include <cmath>

namespace PhotonSim
{

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

PrimaryGeneratorAction::PrimaryGeneratorAction()
{
  G4int n_particle = 1;
  fParticleGun = new G4ParticleGun(n_particle);

  // Create messenger for UI commands
  fMessenger = new PrimaryGeneratorMessenger(this);

  // Default particle: electron with 5 MeV energy
  G4ParticleTable* particleTable = G4ParticleTable::GetParticleTable();
  G4ParticleDefinition* particle = particleTable->FindParticle("e-");
  fParticleGun->SetParticleDefinition(particle);
  
  // Set particle direction along z-axis (0,0,1)
  fParticleGun->SetParticleMomentumDirection(G4ThreeVector(0., 0., 1.));
  
  // Set particle position at the center of the detector (0,0,0)
  fParticleGun->SetParticlePosition(G4ThreeVector(0., 0., 0.));
  
  // Set default energy
  fParticleGun->SetParticleEnergy(5.0 * MeV);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

PrimaryGeneratorAction::~PrimaryGeneratorAction()
{
  delete fMessenger;
  delete fParticleGun;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void PrimaryGeneratorAction::GeneratePrimaries(G4Event* event)
{
  // GENIE mode: emit one final-state primary per G4 event. Each rootracker
  // entry contributes its status==1 particles, one per G4 event, sharing a
  // single per-entry random rotation (so the primaries from one interaction
  // keep their relative kinematics). When the current entry's particles are
  // exhausted we advance to the next rootracker entry; when all entries are
  // exhausted we emit an empty event and print a warning.
  if (fGenieReader && fGenieReader->IsOpen()) {
    G4ParticleTable* particleTable = G4ParticleTable::GetParticleTable();

    auto advance_entry = [this]() -> bool {
      const long long next = fGenieCurrentEntry + 1;
      if (next >= static_cast<long long>(fGenieReader->GetNumEvents())) {
        return false;  // rootracker exhausted
      }
      if (!fGenieReader->LoadEvent(next)) return false;
      fGenieCurrentEntry = next;
      fGenieNextParticleIdx = 0;
      // Fresh per-entry rotation (same matrix reused for every particle
      // coming out of this entry, so the interaction's geometry is kept).
      if (fGenieIsotropic) {
        const G4double cosT = 2.0 * G4UniformRand() - 1.0;
        const G4double sinT = std::sqrt(1.0 - cosT * cosT);
        const G4double phi  = 2.0 * M_PI * G4UniformRand();
        fGenieRotAxisX = sinT * std::cos(phi);
        fGenieRotAxisY = sinT * std::sin(phi);
        fGenieRotAxisZ = cosT;
        fGenieRotAngle = 2.0 * M_PI * G4UniformRand();
      }
      return true;
    };

    // Find the next usable primary: advance entry as needed, skip particles
    // G4 doesn't know (exotic nuclear remnants).
    while (true) {
      if (fGenieCurrentEntry < 0 ||
          fGenieNextParticleIdx >= fGenieReader->FinalStateParticles().size()) {
        if (!advance_entry()) {
          G4cerr << "PrimaryGeneratorAction: GENIE rootracker exhausted at G4 event "
                 << event->GetEventID() << "; emitting empty event." << G4endl;
          return;
        }
        continue;
      }
      const auto& particles = fGenieReader->FinalStateParticles();
      const auto& p = particles[fGenieNextParticleIdx];
      ++fGenieNextParticleIdx;

      G4ParticleDefinition* pdef = particleTable->FindParticle(p.pdg);
      if (!pdef) {
        // Unknown to G4 (e.g., heavy nuclear fragment) — skip and try
        // next. This is the only unavoidable filter: G4 cannot create
        // a particle it doesn't know about. Every other primary
        // (including neutrons and sub-Cherenkov-threshold charged
        // particles) is propagated; LUCiD handles 0-photon events
        // downstream by storing a zero-filled v3 entry.
        continue;
      }

      G4ThreeVector mom(p.px * MeV, p.py * MeV, p.pz * MeV);
      if (fGenieIsotropic) {
        G4RotationMatrix rot;
        rot.rotate(fGenieRotAngle,
                   G4ThreeVector(fGenieRotAxisX, fGenieRotAxisY, fGenieRotAxisZ));
        mom = rot * mom;
      }

      auto* vertex = new G4PrimaryVertex(G4ThreeVector(0., 0., 0.), 0.0);
      auto* primary = new G4PrimaryParticle(pdef, mom.x(), mom.y(), mom.z());
      vertex->SetPrimary(primary);
      event->AddPrimaryVertex(vertex);

      // Per-primary kinetic energy (like particle-gun mode).
      const G4double mass = pdef->GetPDGMass();
      const G4double pmag2 = mom.mag2();
      fTrueEnergy = std::sqrt(pmag2 + mass * mass) - mass;
      return;
    }
  }

  // Helper lambda to generate random direction
  auto generateRandomDirection = [this]() -> G4ThreeVector {
    if (fRandomDirection) {
      // Use Marsaglia method for uniform distribution on sphere
      G4double cosTheta = 2.0 * G4UniformRand() - 1.0;  // cos(theta) in [-1, 1]
      G4double sinTheta = std::sqrt(1.0 - cosTheta * cosTheta);
      G4double phi = 2.0 * M_PI * G4UniformRand();  // phi in [0, 2π]

      return G4ThreeVector(
        sinTheta * std::cos(phi),
        sinTheta * std::sin(phi),
        cosTheta
      );
    } else {
      // Default: fire along z-axis
      return G4ThreeVector(0., 0., 1.);
    }
  };

  // Always fire from center of detector
  fParticleGun->SetParticlePosition(G4ThreeVector(0., 0., 0.));

  // If we have a heterogeneous primary list, use it
  if (!fPrimaryList.empty()) {
    G4ParticleTable* particleTable = G4ParticleTable::GetParticleTable();

    for (const auto& spec : fPrimaryList) {
      // Set particle type
      G4ParticleDefinition* particle = particleTable->FindParticle(spec.particleName);
      if (particle) {
        fParticleGun->SetParticleDefinition(particle);
      } else {
        G4cerr << "Warning: Particle " << spec.particleName << " not found!" << G4endl;
        continue;
      }

      // Set energy (random or fixed depending on spec)
      G4double particleEnergy;
      if (spec.useRandomEnergy) {
        // Sample uniformly from [minEnergy, maxEnergy]
        particleEnergy = spec.minEnergy + (spec.maxEnergy - spec.minEnergy) * G4UniformRand();
      } else {
        particleEnergy = spec.energy;
      }
      fParticleGun->SetParticleEnergy(particleEnergy);
      fTrueEnergy = particleEnergy;

      // Set direction (random or default)
      fParticleGun->SetParticleMomentumDirection(generateRandomDirection());

      // Generate the primary vertex
      fParticleGun->GeneratePrimaryVertex(event);
    }
  }
  // Otherwise, use the original behavior: generate fNumberOfPrimaries copies of the same particle
  else {
    for (G4int i = 0; i < fNumberOfPrimaries; i++) {
      // Generate random energy if requested
      if (fRandomEnergy) {
        fTrueEnergy = fMinEnergy + (fMaxEnergy - fMinEnergy) * G4UniformRand();
        fParticleGun->SetParticleEnergy(fTrueEnergy);
      } else {
        fTrueEnergy = fParticleGun->GetParticleEnergy();
      }

      // Set direction (random or default)
      fParticleGun->SetParticleMomentumDirection(generateRandomDirection());

      // Generate the primary vertex
      fParticleGun->GeneratePrimaryVertex(event);
    }
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void PrimaryGeneratorAction::SetParticleType(const G4String& particleName)
{
  G4ParticleTable* particleTable = G4ParticleTable::GetParticleTable();
  G4ParticleDefinition* particle = particleTable->FindParticle(particleName);
  if (particle) {
    fParticleGun->SetParticleDefinition(particle);
  }
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void PrimaryGeneratorAction::SetParticleEnergy(G4double energy)
{
  fParticleGun->SetParticleEnergy(energy);
  fRandomEnergy = false;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void PrimaryGeneratorAction::SetEnergyRange(G4double minEnergy, G4double maxEnergy)
{
  fMinEnergy = minEnergy;
  fMaxEnergy = maxEnergy;
  fRandomEnergy = true;
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void PrimaryGeneratorAction::SetParticlePosition(const G4ThreeVector& position)
{
  fParticleGun->SetParticlePosition(position);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void PrimaryGeneratorAction::SetParticleDirection(const G4ThreeVector& direction)
{
  fParticleGun->SetParticleMomentumDirection(direction);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void PrimaryGeneratorAction::AddPrimary(const G4String& particleName, G4double energy)
{
  PrimaryParticleSpec spec;
  spec.particleName = particleName;
  spec.energy = energy;
  spec.useRandomEnergy = false;
  fPrimaryList.push_back(spec);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void PrimaryGeneratorAction::AddPrimaryWithEnergyRange(const G4String& particleName, G4double minEnergy, G4double maxEnergy)
{
  PrimaryParticleSpec spec;
  spec.particleName = particleName;
  spec.minEnergy = minEnergy;
  spec.maxEnergy = maxEnergy;
  spec.useRandomEnergy = true;
  fPrimaryList.push_back(spec);
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

void PrimaryGeneratorAction::SetGenieInput(const G4String& path)
{
  if (!fGenieReader) fGenieReader = std::make_unique<RooTrackerReader>();
  if (!fGenieReader->Open(path)) {
    G4cerr << "PrimaryGeneratorAction: failed to open GENIE input " << path << G4endl;
    fGenieReader.reset();
  } else {
    G4cout << "PrimaryGeneratorAction: opened GENIE rootracker " << path
           << " (" << fGenieReader->GetNumEvents() << " events)" << G4endl;
  }
}

G4bool PrimaryGeneratorAction::HasGenieInput() const
{
  return fGenieReader && fGenieReader->IsOpen();
}

//....oooOO0OOooo........oooOO0OOooo........oooOO0OOooo........oooOO0OOooo......

}  // namespace PhotonSim