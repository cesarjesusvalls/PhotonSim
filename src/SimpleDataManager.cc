//
/// \file PhotonSim/src/SimpleDataManager.cc
/// \brief Simple data manager implementation

#include "SimpleDataManager.hh"
#include "G4SystemOfUnits.hh"
#include "G4ios.hh"

namespace PhotonSim
{

SimpleDataManager* SimpleDataManager::fInstance = nullptr;

SimpleDataManager* SimpleDataManager::GetInstance()
{
  if (!fInstance) {
    fInstance = new SimpleDataManager();
  }
  return fInstance;
}

void SimpleDataManager::Initialize(const G4String& filename)
{
  // Open CSV file for optical photon data
  fOutputFile.open(filename + ".csv");
  if (!fOutputFile.is_open()) {
    G4cerr << "Error: Cannot create output file " << filename << ".csv" << G4endl;
    return;
  }
  
  // Write CSV header
  fOutputFile << "EventID,PrimaryEnergy_MeV,PhotonPosX_mm,PhotonPosY_mm,PhotonPosZ_mm,"
              << "PhotonDirX,PhotonDirY,PhotonDirZ,PhotonTime_ns,Process" << G4endl;
  
  // Open summary file
  fSummaryFile.open(filename + "_summary.csv");
  if (fSummaryFile.is_open()) {
    fSummaryFile << "EventID,PrimaryEnergy_MeV,NOpticalPhotons" << G4endl;
  }
  
  fInitialized = true;
  G4cout << "Simple data output files created: " << filename << ".csv and " 
         << filename << "_summary.csv" << G4endl;
}

void SimpleDataManager::Finalize()
{
  if (fOutputFile.is_open()) {
    fOutputFile.close();
    G4cout << "Optical photon data file closed." << G4endl;
  }
  
  if (fSummaryFile.is_open()) {
    fSummaryFile.close();
    G4cout << "Summary data file closed." << G4endl;
  }
}

void SimpleDataManager::BeginEvent(G4int eventID, G4double primaryEnergy)
{
  fCurrentEventID = eventID;
  fCurrentPrimaryEnergy = primaryEnergy / MeV; // Store in MeV
  fPhotonCount = 0;
}

void SimpleDataManager::EndEvent()
{
  // Write summary data
  if (fSummaryFile.is_open()) {
    fSummaryFile << fCurrentEventID << "," << fCurrentPrimaryEnergy << "," 
                 << fPhotonCount << G4endl;
  }
}

void SimpleDataManager::AddOpticalPhoton(G4double x, G4double y, G4double z,
                                        G4double dx, G4double dy, G4double dz,
                                        G4double time, const G4String& process)
{
  if (!fInitialized || !fOutputFile.is_open()) return;
  
  // Write optical photon data to CSV
  fOutputFile << fCurrentEventID << "," 
              << fCurrentPrimaryEnergy << ","
              << x/mm << "," << y/mm << "," << z/mm << ","
              << dx << "," << dy << "," << dz << ","
              << time/ns << "," << process << G4endl;
  
  fPhotonCount++;
}

}  // namespace PhotonSim