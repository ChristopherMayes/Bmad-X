import yaml

import torch
import numpy as np

import distgen
from distgen import Generator
from distgen.physical_constants import unit_registry as unit

from bmadx.constants import M_ELECTRON
from bmadx.coordinates import openpmd_to_bmadx
from bmadx.bmad_torch.track_torch import Beam

def create_pmd_particlegroup(base_yaml, transforms_yaml):
    '''Creates openPMD ParticleGroup from dist and transform yaml files
    using distgen

    Args: 
        base_yaml: yaml file with base distribution parameters
        transform_yaml: yaml file with transforms
    
    Returns:
        generated openPMD ParticleGroup
    '''
    
    gen = Generator(base_yaml)

    with open(transforms_yaml) as f:
        transforms_dict = yaml.safe_load(f)

    if distgen.__version__ >= '1.0.0':
        gen["transforms"] = transforms_dict
    else:
        gen.input["transforms"] = transforms_dict

    particle_group = gen.run()
    particle_group.drift_to_z(z=0)

    return particle_group

def create_beam(base_yaml, transforms_yaml, p0c, fname=None):
    '''Creates bmadx torch Beam from dist and transform yaml files
    using distgen

    Args: 
        base_yaml: yaml file with base distribution parameters
        transform_yaml: yaml file with transforms
        p0c: reference momentum of Beam coordinates in eV
        fname (str): if provided, saves the generated Beam
    
    Returns:
        generated Bmad-X torch Beam. 
    '''

    # Generate openPMD particle group:
    particle_group = create_pmd_particlegroup(base_yaml, transforms_yaml)

    # Transform to Bmad phase space coordinates:
    coords = np.array(openpmd_to_bmadx(particle_group, p0c)).T
    tkwargs = {"dtype": torch.float32}
    coords = torch.tensor(coords, **tkwargs)

    # create Bmad-X torch Beam:
    beam = Beam(
        coords,
        s=torch.tensor(0.0, **tkwargs),
        p0c=torch.tensor(p0c, **tkwargs),
        mc2=torch.tensor(M_ELECTRON, **tkwargs)
    )

    # save ground truth beam
    if fname is not None:

        torch.save(beam, fname)
        print(f'ground truth distribution saved at {fname}')

    return beam
