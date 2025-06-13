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
// * acceptance of all terms of the Geant4 Software license.          *
// ********************************************************************
//
//
/// \file PhotonSim/include/PhysicsList.hh
/// \brief Definition of the PhotonSim::PhysicsList class

#ifndef OpticalPhysicsList_h
#define OpticalPhysicsList_h 1

#include "G4VModularPhysicsList.hh"

namespace PhotonSim
{

/// Physics list including standard electromagnetic processes and optical physics

class PhysicsList : public G4VModularPhysicsList
{
  public:
    PhysicsList();
    ~PhysicsList() override = default;

    void ConstructParticle() override;
    void ConstructProcess() override;
    void SetCuts() override;
};

}  // namespace PhotonSim

#endif