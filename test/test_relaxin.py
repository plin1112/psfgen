#/usr/bin/env python
"""
Tests a simple protein with many disulfides: disulfides between two identical
resids on different chains, disulfides on the same chain, and unrelated
disulfides on different chains.
"""
import pytest
import os
from vmd import atomsel, molecule

dir = os.path.dirname(__file__)

#==============================================================================

def check_correctness(molid):
    """ Verifies molecule is sane """

    molecule.set_top(molid)

    # Check the protein is there with the correct capping groups
    assert len(atomsel("protein or resname ACE NMA NME")) == 828
    assert len(set(atomsel("protein").get("fragment"))) == 2
    assert len(set(atomsel("resname ACE NMA NME").get("residue"))) == 4

    # Check for 6 cysteines, 2 with same resid
    assert len(set(atomsel("resname CYS CYX").get("residue"))) == 6

    # Check connectivity between cysteines is correct
    for res in set(atomsel("resname CYS CYX").get("residue")):
        assert len(atomsel("residue %d" % res)) == 10
        assert len(atomsel("residue %d and name SG" % res)) == 1
        idxs = atomsel("residue %d and name SG" % res).bonds[0]
        assert set(atomsel("index %s"
                           % " ".join(str(i) for i in idxs)).get("name")) \
            == set(["CB", "SG"])

#==============================================================================

def test_query():
    """
    Tests that query functions work correctly
    """

    from psfgen import PsfGen
    gen = PsfGen(output=os.devnull)
    os.chdir(dir)

    gen.read_topology("top_all36_caps.rtf")
    gen.read_topology("top_all36_prot.rtf")

    gen.add_segment(segid="P0", pdbfile="psf_protein_P0.pdb")
    gen.read_coords(segid="P0", filename="psf_protein_P0.pdb")

    gen.add_segment(segid="P1", pdbfile="psf_protein_P1.pdb")
    gen.read_coords(segid="P1", filename="psf_protein_P1.pdb")

    gen.patch(patchname="DISU", targets=[("P0","10"), ("P0","15")])

    assert gen.get_topologies() == ["top_all36_caps.rtf",
                                    "top_all36_prot.rtf"]

    # Check residue names query
    resnames = gen.get_residue_types()
    assert len(resnames) == 26
    assert "CYS" in resnames
    assert "TIP3" not in resnames

    # Check patches query
    patches = gen.get_patches(list_all=True)
    assert len(patches) == 25
    assert "CYSD" in patches
    assert "SEP" not in patches

    # Check segids query
    assert gen.get_segids() == ["P0", "P1"]

    # Check resids query
    assert gen.get_resids("P0") == [str(_) for _ in range(1, 26)]
    assert gen.get_resids("P1") == [str(_) for _ in range(0, 31)]

    # Check resname query, with str or int
    assert gen.get_resname(segid="P0", resid="2") == "LEU"
    assert gen.get_resname(segid="P1", resid=29) == "SER"

    # Check applied patches query
    assert gen.get_patches() == [("DISU","P0","10"), ("DISU","P0","15")]
    assert gen.get_first(segid="P0") is None
    assert gen.get_last(segid="P1") is None

    # Check atom queries
    assert gen.get_atom_names(segid="P0", resid="10") \
                == ['N', 'HN', 'CA', 'HA', 'CB', 'HB1', 'HB2', 'SG', 'C', 'O']
    assert set(gen.get_masses(segid="P0", resid=1)) == {1.008, 12.011, 15.999}
    assert gen.get_atom_indices(segid="P1", resid=0) == list(range(1,7))
    assert set(gen.get_charges(segid="P0", resid="10")) \
        == {-0.47, 0.07, 0.09, 0.31, -0.1, -0.08, 0.51, -0.51}

    # Check coordinates and velocities
    assert len(gen.get_coordinates(segid="P1", resid=25)) == 17
    assert set(gen.get_velocities(segid="P1", resid=1)) == {(0.,0.,0.)}

#==============================================================================

def test_set():
    """
    Tests that setters work correctly
    """
    from psfgen import PsfGen
    os.chdir(dir)

    gen = PsfGen(output=os.devnull)
    gen.read_topology("top_all36_caps.rtf")
    gen.read_topology("top_all36_prot.rtf")

    gen.add_segment(segid="P", pdbfile="psf_protein_P1.pdb")
    assert gen.get_segids() == ["P"]

    # Set segid
    gen.set_segid(segid="P", new_segid="P1")
    assert gen.get_segids() == ["P1"]

    gen.read_coords(segid="P1", filename="psf_protein_P1.pdb")

    # Set resname
    assert gen.get_resname(segid="P1", resid="1") == "ASP"
    gen.set_resname(segid="P1", resid="1", new_resname="ASH")
    assert gen.get_resname(segid="P1", resid="1") == "ASH"

    # Set charge
    gen.set_charge(segid="P1", resid="1", atomname="O", charge=-1.)
    assert -1.0 in gen.get_charges(segid="P1", resid="1")

    # Set atom name
    gen.set_atom_name(segid="P1", resid="1", atomname="N", new_atomname="NO")
    assert "N" not in gen.get_atom_names(segid="P1", resid="1")
    assert "NO" in gen.get_atom_names(segid="P1", resid="1")

    # Set coord
    gen.set_position(segid="P1", resid="1", atomname="HN",
                  position=(0.,0.,-1.))
    assert (0., 0., -1.) in gen.get_coordinates(segid="P1", resid="1")

    # Set velocity
    gen.set_velocity(segid="P1", resid="1", atomname="NO",
                     velocity=(5., 5., 3.,))
    assert (5., 5., 3.,) in gen.get_velocities(segid="P1", resid="1")

#==============================================================================

def test_alias():
    """
    Tests atom and residue aliases, either at the topology or the PDB level
    """
    from psfgen import PsfGen
    os.chdir(dir)

    gen = PsfGen(output=os.devnull)
    gen.read_topology("top_all36_caps.rtf")
    gen.read_topology("top_all36_prot.rtf")

    gen.alias_residue(top_resname="LEU", pdb_resname="LEX")
    gen.alias_residue(top_resname="ARG", pdb_resname="AAA")
    gen.alias_atom(top_atomname="N", pdb_atomname="NOOO", resname="PHE")

    gen.add_segment(segid="P", pdbfile="protein_newnames.pdb")
    gen.read_coords(segid="P", filename="psf_protein_P0.pdb")

    assert gen.get_resname(segid="P", resid=2) == "LEU"
    assert gen.get_resname(segid="P", resid=5) == "ALA"
    assert "N" in gen.get_atom_names(segid="P", resid=23)

#==============================================================================

def test_ends(tmpdir):
    """
    Tests adding patches to the beginning and end, as well as adding
    residues in the segment
    """
    from psfgen import PsfGen
    p = str(tmpdir.mkdir("mutation"))
    os.chdir(dir)

    gen = PsfGen(output=os.devnull)
    gen.read_topology("top_all36_prot.rtf")

    # Add neutral N-terminus
    # Add an alanine then a protonated glutamate at the C-terminus.
    gen.add_segment(segid="P", pdbfile="protein_nocaps.pdb",
                    first="NTER", last="GLUP",
                    residues=[("25", "ALA"), ("26", "GLU")])

    # Set coordinates and regenerate angles and dihedrals
    gen.read_coords(segid="P", filename="protein_nocaps.pdb")
    gen.guess_coords()

    # Check internal state
    assert gen.get_resids("P") == [str(_) for _ in range(2, 27)]
    assert gen.get_resname(segid="P", resid=25) == "ALA"
    assert gen.get_patches(list_defaults=True) == [('GLUP', 'P', '26'),
                                                   ('NTER', 'P', '2')]
    assert gen.get_first(segid="P") == "NTER"
    assert gen.get_last(segid="P") == "GLUP"

    # Output
    os.chdir(p)
    gen.write_psf(filename="output.psf")
    gen.write_pdb(filename="output.pdb")

    # Check all resids are present and that 2 extra ones were added
    m = molecule.load("psf", "output.psf", "pdb", "output.pdb")
    assert list(set(atomsel("all").get("resid"))) == list(range(2, 27))
    assert len(atomsel("all")) == 382
    assert set(atomsel("resid 25").get("resname")) == set(["ALA"])

    # Check patches were applied correctly
    assert "HT1" in atomsel("resid 2").get("name")
    assert "HN" not in atomsel("resid 2").get("name")
    assert "HE2" in atomsel("resid 26").get("name")

    # Check all coordinates are set
    assert 0.0 not in atomsel("all").get("x")
    assert 0.0 not in atomsel("all").get("y")
    assert 0.0 not in atomsel("all").get("z")

    molecule.delete(m)

#==============================================================================

def test_mutation(tmpdir):
    """
    Tests mutation of L2A in chain 0. Also as a result tests guessing
    coordinates
    """
    from psfgen import PsfGen
    p = str(tmpdir.mkdir("mutation"))
    os.chdir(dir)

    gen = PsfGen(output=os.devnull)
    gen.read_topology("top_all36_caps.rtf")
    gen.read_topology("top_all36_prot.rtf")

    gen.add_segment(segid="P0", pdbfile="psf_protein_P0.pdb",
                    mutate=[("2", "ALA")])
    gen.read_coords(segid="P0", filename="psf_protein_P0.pdb")
    gen.patch(patchname="DISU", targets=[("P0","10"), ("P0","15")])

    # Guess coordinates for ALA mutation
    gen.guess_coords()

    # Set one specific coordinate
    gen.set_position(segid="P0", resid="2", atomname="HB1",
                     position=(1.0,2.0,3.0))

    # Regenerate
    gen.regenerate_angles()
    gen.regenerate_dihedrals()

    # Write
    os.chdir(p)
    gen.write_psf(filename="output.psf")
    gen.write_pdb(filename="output.pdb")

    # Check results with vmd-python
    m = molecule.load("psf", "output.psf", "pdb", "output.pdb")
    assert len(set(atomsel("protein").get("fragment"))) == 1
    assert len(set(atomsel("resname ACE NMA NME").get("residue"))) == 2

    # Test mutation happened and resid 2 is ALA not LEU
    assert set(atomsel("resid 2").get("resname")) == set(["ALA"])

    # Check coordinate guessing happened and HB3 has a nonzero position
    assert atomsel("resid 2 and name HB3").get("x") != [0.0]
    assert atomsel("resid 2 and name HB3").get("y") != [0.0]
    assert atomsel("resid 2 and name HB3").get("z") != [0.0]

    # Check manual coordinate setting happened
    assert atomsel("resid 2 and name HB1").get("x") == [1.0]
    assert atomsel("resid 2 and name HB1").get("y") == [2.0]
    assert atomsel("resid 2 and name HB1").get("z") == [3.0]

    molecule.delete(m)

#===============================================================================

def test_delete():
    """
    Tests removing atoms
    """
    from psfgen import PsfGen
    os.chdir(dir)

    gen = PsfGen(output=os.devnull)
    gen.read_topology("top_all36_caps.rtf")
    gen.read_topology("top_all36_prot.rtf")

    gen.add_segment(segid="P0", pdbfile="psf_protein_P0.pdb")
    gen.read_coords(segid="P0", filename="psf_protein_P0.pdb")

    # Delete a specific atom
    assert "CAY" in gen.get_atom_names(segid="P0", resid=1)
    gen.delete_atoms(segid="P0", resid=1, atomname="CAY")
    assert "CAY" not in gen.get_atom_names(segid="P0", resid=1)

    # Try deleting a capping group
    assert gen.get_resids("P0") == [str(_) for _ in range(1,26)]
    gen.delete_atoms(segid="P0", resid=1)
    assert gen.get_resids("P0") == [str(_) for _ in range(2,26)]

    # Add and then delete a segment
    gen.add_segment(segid="DELETE", pdbfile="psf_protein_P1.pdb")
    assert gen.get_segids() == ["P0", "DELETE"]
    gen.delete_atoms(segid="DELETE")
    assert gen.get_segids() == ["P0"]


#===============================================================================

def test_case_sensitivity():
    """
    Tests setting case sensitivity. Do this with 2 objects because you can't
    change the setting after reading in topology files.
    """

    from psfgen import PsfGen
    os.chdir(dir)

    gen = PsfGen(case_sensitive=True, output=os.devnull)
    gen.read_topology("top_casesensitive.rtf")
    assert gen.get_residue_types() == ["ACE", "Ace"]

    # Can't change case sensitivity after topologies have been read
    with pytest.raises(ValueError):
        gen.case_sensitive = False
    del gen

    gen = PsfGen(case_sensitive=True, output=os.devnull)
    gen.case_sensitive = False
    gen.read_topology("top_casesensitive.rtf")
    assert gen.get_residue_types() == ["ACE"]

#===============================================================================

def test_single_chain(tmpdir):
    """
    Tests simple realistic system building
    """

    from psfgen import PsfGen
    p = str(tmpdir.mkdir("single_chain"))
    os.chdir(dir)

    gen = PsfGen(output=os.devnull)
    gen.read_topology("top_all36_caps.rtf")
    gen.read_topology("top_all36_prot.rtf")
    gen.read_topology("top_water_ions.rtf")

    # Read protein
    gen.add_segment(segid="P0", pdbfile="psf_protein_P0.pdb")
    gen.read_coords(segid="P0", filename="psf_protein_P0.pdb")

    gen.add_segment(segid="P1", pdbfile="psf_protein_P1.pdb")
    gen.read_coords(segid="P1", filename="psf_protein_P1.pdb")

    # Read waters, with 10k atoms per file to avoid PDB limitations
    gen.add_segment(segid="W0", pdbfile="psf_wat_0.pdb")
    gen.read_coords(segid="W0", filename="psf_wat_0.pdb")

    gen.add_segment(segid="W1", pdbfile="psf_wat_1.pdb")
    gen.read_coords(segid="W1", filename="psf_wat_1.pdb")

    # Read ions
    gen.add_segment(segid="I", pdbfile="psf_ions.pdb")
    gen.read_coords(segid="I", filename="psf_ions.pdb")

    # Add disulfides
    gen.patch(patchname="DISU", targets=[("P0","10"), ("P0","15")])
    gen.patch(patchname="DISU", targets=[("P0","24"), ("P1","23")])
    gen.patch(patchname="DISU", targets=[("P0","11"), ("P1","11")])

    # Regenerate
    gen.regenerate_angles()
    gen.regenerate_dihedrals()

    # Write
    os.chdir(p)
    gen.write_psf(filename="output.psf")
    gen.write_pdb(filename="output.pdb")

    # Load as a molecule with vmd-python and check it's correct
    m = molecule.load("psf", "output.psf", "pdb", "output.pdb")
    check_correctness(m)
    molecule.delete(m)

#===============================================================================

def test_formats(tmpdir):
    """
    Tests read/write of psf/namdbin files
    """

    from psfgen import PsfGen
    p = str(tmpdir.mkdir("formats"))
    os.chdir(dir)

    gen = PsfGen(output=os.devnull)
    gen.read_topology("top_all36_caps.rtf")
    gen.read_topology("top_all36_prot.rtf")

    gen.add_segment(segid="P0", pdbfile="psf_protein_P0.pdb")
    gen.read_coords(segid="P0", filename="psf_protein_P0.pdb")
    gen.add_segment(segid="P1", pdbfile="psf_protein_P1.pdb")
    gen.read_coords(segid="P1", filename="psf_protein_P1.pdb")

    # Write a PSF and a NAMD binary file
    gen.write_psf(filename=os.path.join(p, "pdbin.psf"))
    gen.write_namdbin(filename=os.path.join(p, "pdbin.bin"))
    del gen

    # Read in the PSF and NAMD binary file. Topology files should be
    # automatically loaded, too. Read in coordinates also as velocities
    # to test the velocity read in as well.
    gen = PsfGen(output=os.devnull)
    os.chdir(p)
    gen.read_psf(filename=os.path.join(p, "pdbin.psf"),
                 namdbinfile=os.path.join(p, "pdbin.bin"),
                 velnamdbinfile=os.path.join(p, "pdbin.bin"))
    assert gen.get_topologies() == ["top_all36_caps.rtf",
                                    "top_all36_prot.rtf"]
    assert gen.get_segids() == ["P0", "P1"]
    assert gen.get_coordinates(segid="P0", resid=1) \
        == gen.get_velocities(segid="P0", resid=1)

#==============================================================================
