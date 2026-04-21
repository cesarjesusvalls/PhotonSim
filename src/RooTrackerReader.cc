#include "RooTrackerReader.hh"

#include "G4SystemOfUnits.hh"
#include "globals.hh"

#include "TFile.h"
#include "TTree.h"

#include <cmath>

namespace PhotonSim
{

RooTrackerReader::RooTrackerReader() = default;

RooTrackerReader::~RooTrackerReader()
{
  if (fFile) {
    fFile->Close();
    delete fFile;
    fFile = nullptr;
    fTree = nullptr;
  }
}

G4bool RooTrackerReader::Open(const std::string& path)
{
  if (fFile) {
    fFile->Close();
    delete fFile;
    fFile = nullptr;
    fTree = nullptr;
  }

  fPath = path;
  fFile = TFile::Open(path.c_str(), "READ");
  if (!fFile || fFile->IsZombie()) {
    G4cerr << "RooTrackerReader: cannot open " << path << G4endl;
    if (fFile) { delete fFile; fFile = nullptr; }
    return false;
  }
  fTree = dynamic_cast<TTree*>(fFile->Get("gRooTracker"));
  if (!fTree) {
    G4cerr << "RooTrackerReader: TTree 'gRooTracker' not found in " << path << G4endl;
    fFile->Close();
    delete fFile;
    fFile = nullptr;
    return false;
  }

  fTree->SetBranchAddress("StdHepN",       &fStdHepN);
  fTree->SetBranchAddress("StdHepPdg",     fStdHepPdg);
  fTree->SetBranchAddress("StdHepStatus",  fStdHepStatus);
  fTree->SetBranchAddress("StdHepP4",      fStdHepP4);
  return true;
}

Long64_t RooTrackerReader::GetNumEvents() const
{
  return fTree ? fTree->GetEntries() : 0;
}

G4bool RooTrackerReader::LoadEvent(Long64_t i)
{
  fFinalState.clear();
  fNuKE_MeV = 0.0;
  fNuPdg = 0;

  if (!fTree) return false;
  const Long64_t n = fTree->GetEntries();
  if (i < 0 || i >= n) {
    G4cerr << "RooTrackerReader: event index " << i << " out of range [0," << n << ")" << G4endl;
    return false;
  }

  if (fTree->GetEntry(i) <= 0) {
    G4cerr << "RooTrackerReader: failed to read entry " << i << G4endl;
    return false;
  }

  const int np = (fStdHepN < kMaxParticles) ? fStdHepN : kMaxParticles;
  for (int k = 0; k < np; ++k) {
    const int status = fStdHepStatus[k];
    const int pdg = fStdHepPdg[k];
    // GeV -> MeV
    const double px = fStdHepP4[k][0] * 1000.0;
    const double py = fStdHepP4[k][1] * 1000.0;
    const double pz = fStdHepP4[k][2] * 1000.0;
    const double E  = fStdHepP4[k][3] * 1000.0;

    if (status == 0 && (pdg == 12 || pdg == -12 || pdg == 14 || pdg == -14 || pdg == 16 || pdg == -16)) {
      // Incoming neutrino (initial state): use as true primary energy.
      // Massless for practical purposes at the scales here — store |p| as KE.
      const double p = std::sqrt(px*px + py*py + pz*pz);
      fNuKE_MeV = p;
      fNuPdg = pdg;
    }

    if (status != 1) continue;
    fFinalState.push_back({pdg, px, py, pz, E});
  }

  return true;
}

}  // namespace PhotonSim
