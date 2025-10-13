# PhotonSim S3DF Job Scripts

This directory contains scripts for submitting and managing PhotonSim jobs on the S3DF cluster.

## Scripts Overview

### Job Submission Scripts

#### 1. submit_photonsim_job.sh
Submit a single PhotonSim job with **fixed energy** and **averaged photon data** (no individual photon storage).

```bash
./submit_photonsim_job.sh -p <particle> -n <nevents> -e <energy> -o <output_dir> [-f <filename>]
```

Options:
- `-p`: Particle type (default: mu-)
- `-n`: Number of events (default: 1000)
- `-e`: Energy in MeV (default: 1000)
- `-o`: Output directory (required)
- `-f`: Output filename (default: output.root)

**Physics**: Disables muon and pion decay processes. Individual photon storage is **disabled**.

Example:
```bash
./submit_photonsim_job.sh -p mu- -n 10000 -e 1000 -o /sdf/data/neutrino/cjesus/photonsim_output/water/monoenergetic/averaged
```

#### 2. submit_photonsim_batch.sh
Submit multiple averaged photon jobs from a configuration file.

```bash
./submit_photonsim_batch.sh -c <config_file> [-s] [-t]
```

Options:
- `-c`: Configuration file (required)
- `-s`: Submit jobs to SLURM (default: prepare only)
- `-t`: Test mode - create only one job

Configuration file format (one job per line):
```
particle nevents energy output_dir [filename]
```

Example:
```bash
# Prepare jobs without submitting
./submit_photonsim_batch.sh -c muons_100_2000_10k.txt

# Prepare and submit all jobs
./submit_photonsim_batch.sh -c muons_100_2000_10k.txt -s

# Test with first job only
./submit_photonsim_batch.sh -c muons_100_2000_10k.txt -t
```

---

#### 3. submit_photonsim_job_individual.sh
Submit a single PhotonSim job with **fixed energy** and **individual photon storage enabled**.

```bash
./submit_photonsim_job_individual.sh -p <particle> -n <nevents> -e <energy> -o <output_dir> [-f <filename>]
```

Options:
- `-p`: Particle type (default: mu-)
- `-n`: Number of events (default: 100)
- `-e`: Energy in MeV (default: 1000)
- `-o`: Output directory (required)
- `-f`: Output filename (default: output.root)

**Physics**: Disables muon and pion decay processes. Individual photon storage is **enabled**.

Example:
```bash
./submit_photonsim_job_individual.sh -p mu- -n 100 -e 1050 -o /sdf/data/neutrino/cjesus/photonsim_output/water/monoenergetic/event_by_event -f output_job001.root
```

#### 4. submit_photonsim_batch_individual.sh
Submit multiple event-by-event jobs from a configuration file.

```bash
./submit_photonsim_batch_individual.sh -c <config_file> [-s] [-t]
```

Example:
```bash
# Prepare and submit 100 jobs at 1050 MeV
./submit_photonsim_batch_individual.sh -c muons_1050_100jobs_100events.txt -s
```

---

#### 5. submit_photonsim_job_uniform.sh
Submit a single PhotonSim job with **uniform random energy distribution** and **individual photon storage enabled**.

```bash
./submit_photonsim_job_uniform.sh -p <particle> -n <nevents> -m <min_energy> -M <max_energy> -o <output_dir> [-f <filename>]
```

Options:
- `-p`: Particle type (default: mu-)
- `-n`: Number of events (default: 100)
- `-m`: Minimum energy in MeV (default: 210)
- `-M`: Maximum energy in MeV (default: 1500)
- `-o`: Output directory (required)
- `-f`: Output filename (default: output.root)

**Physics**: Disables muon and pion decay processes. Each event has a uniformly random energy between min and max. Individual photon storage is **enabled**.

Example:
```bash
./submit_photonsim_job_uniform.sh -p mu- -n 100 -m 210 -M 1500 -o /sdf/data/neutrino/cjesus/photonsim_output/water/uniform_energy
```

#### 6. submit_photonsim_batch_uniform.sh
Submit multiple uniform energy jobs from a configuration file.

```bash
./submit_photonsim_batch_uniform.sh -c <config_file> [-s] [-t]
```

Configuration file format (one job per line):
```
particle nevents min_energy max_energy output_dir filename
```

Example:
```bash
# Prepare and submit uniform energy muon jobs
./submit_photonsim_batch_uniform.sh -c muon_uniform_210_1500_MeV_100jobs_100events.txt -s
```

---

#### 7. submit_photonsim_lucid_job_uniform.sh
Submit a single PhotonSim job with **uniform random energy distribution** and **LUCiD processing**.

```bash
./submit_photonsim_lucid_job_uniform.sh -p <particle> -n <nevents> -m <min_energy> -M <max_energy> -o <output_dir> [-f <filename>] [-l <lucid_path>]
```

Options:
- `-p`: Particle type (default: mu-)
- `-n`: Number of events (default: 100)
- `-m`: Minimum energy in MeV (default: 210)
- `-M`: Maximum energy in MeV (default: 1500)
- `-o`: Output directory (required)
- `-f`: Output filename (default: output.root)
- `-l`: LUCiD installation path (default: /sdf/home/c/cjesus/Dev/LUCiD)

**Pipeline**:
1. Runs PhotonSim with uniform energy distribution
2. Runs LUCiD using singularity (develop.sif) to process ROOT files
3. Generates final HDF5 output files (events_jobXXX.h5)

**Physics**: Same as uniform energy jobs. Individual photon storage is **enabled**.

Example:
```bash
./submit_photonsim_lucid_job_uniform.sh -p mu- -n 100 -m 210 -M 1500 -o /sdf/data/neutrino/cjesus/photonsim_output/water/uniform_energy -f output_job001.root
```

#### 8. submit_photonsim_lucid_batch_uniform.sh
Submit multiple PhotonSim + LUCiD jobs from a configuration file.

```bash
./submit_photonsim_lucid_batch_uniform.sh -c <config_file> [-s] [-t] [-l <lucid_path>]
```

Options:
- `-c`: Configuration file (required)
- `-s`: Submit jobs to SLURM (default: prepare only)
- `-t`: Test mode - create only one job
- `-l`: LUCiD installation path (default: /sdf/home/c/cjesus/Dev/LUCiD)

Configuration file format (same as uniform energy):
```
particle nevents min_energy max_energy output_dir filename
```

Example:
```bash
# Generate config using existing generator
./generate_uniform_energy_config.sh -p mu- -n 100

# Prepare and submit with LUCiD processing
./submit_photonsim_lucid_batch_uniform.sh -c muon_uniform_210_1500_MeV_100jobs_100events.txt -s
```

**Output**: Each job produces both `output_jobXXX.root` and `events_jobXXX.h5` files.

---

### Configuration Generator

#### 9. generate_uniform_energy_config.sh
Generate configuration files for uniform energy simulations with **N** jobs as a parameter.

```bash
./generate_uniform_energy_config.sh -p <particle> -n <njobs> [-e <nevents>] [-o <output_dir>]
```

Options:
- `-p`: Particle type (mu- or pi+) (required)
- `-n`: Number of jobs to generate (required)
- `-e`: Number of events per job (default: 100)
- `-o`: Output directory (default: /sdf/data/neutrino/cjesus/photonsim_output/water/uniform_energy)

**Energy ranges** (Cherenkov threshold + 50 MeV to 1500 MeV):
- **mu-**: 210-1500 MeV (threshold at 160.3 MeV)
- **pi+**: 262-1500 MeV (threshold at 211.8 MeV)

Example:
```bash
# Generate config for 100 muon jobs
./generate_uniform_energy_config.sh -p mu- -n 100

# Generate config for 50 pion jobs with 200 events each
./generate_uniform_energy_config.sh -p pi+ -n 50 -e 200
```

This creates a configuration file like `muon_uniform_210_1500_MeV_100jobs_100events.txt` that can be used with `submit_photonsim_batch_uniform.sh`.

---

### Job Management Scripts

#### 10. monitor_jobs.sh
Monitor PhotonSim jobs running on S3DF.

```bash
./monitor_jobs.sh [-a] [-w] [-o output_dir]
```

Options:
- `-a`: Show all jobs (default: only PhotonSim jobs)
- `-w`: Watch mode - refresh every 30 seconds
- `-o`: Check specific output directory for results

Example:
```bash
# Monitor PhotonSim jobs in watch mode
./monitor_jobs.sh -w -o /sdf/data/neutrino/cjesus/photonsim_output/water
```

#### 11. cleanup_jobs.sh
Clean up job-related files (logs, macros, scripts) while preserving ROOT output files.

```bash
./cleanup_jobs.sh -o <output_dir> [-l] [-m] [-s] [-a]
```

Options:
- `-o`: Output directory to clean (required)
- `-l`: Clean log files (job-*.out, job-*.err)
- `-m`: Clean macro files (*.mac)
- `-s`: Clean script files (*.sh, *.sbatch)
- `-a`: Clean all (logs, macros, and scripts)

**Note**: By default runs in dry-run mode. Edit the script to set `DRY_RUN=false` to actually delete files.

Example:
```bash
# See what would be cleaned (dry run)
./cleanup_jobs.sh -o /sdf/data/neutrino/cjesus/photonsim_output/water/monoenergetic/averaged -a

# Clean only log files
./cleanup_jobs.sh -o /sdf/data/neutrino/cjesus/photonsim_output/water/uniform_energy -l
```

## Directory Structure

The recommended directory structure organizes simulations by medium, energy type, and data storage mode:

```
/sdf/data/neutrino/cjesus/photonsim_output/
├── water/
│   ├── monoenergetic/
│   │   ├── averaged/              # Fixed energy, averaged photon data (no individual storage)
│   │   │   ├── mu-/
│   │   │   │   ├── 100MeV/
│   │   │   │   │   ├── output.root
│   │   │   │   │   ├── run_*.mac
│   │   │   │   │   ├── run_photonsim.sh
│   │   │   │   │   ├── submit_job.sbatch
│   │   │   │   │   ├── job-*.out
│   │   │   │   │   └── job-*.err
│   │   │   │   ├── 110MeV/
│   │   │   │   └── ...
│   │   │   └── pi+/
│   │   │       └── ...
│   │   └── event_by_event/        # Fixed energy, individual photon storage enabled
│   │       ├── mu-/
│   │       │   ├── 1050MeV/
│   │       │   │   ├── output_job001.root
│   │       │   │   ├── output_job002.root
│   │       │   │   ├── ...
│   │       │   │   └── run_*.mac
│   │       │   └── ...
│   │       └── pi+/
│   │           └── ...
│   └── uniform_energy/            # Uniform energy distribution, individual photon storage enabled
│       ├── mu-/
│       │   ├── 210_1500MeV_uniform/
│       │   │   ├── output_job001.root      # PhotonSim ROOT output
│       │   │   ├── output_job002.root
│       │   │   ├── events_job001.h5         # LUCiD HDF5 output (if using LUCiD scripts)
│       │   │   ├── events_job002.h5
│       │   │   ├── ...
│       │   │   └── run_*.mac
│       │   └── ...
│       └── pi+/
│           ├── 262_1500MeV_uniform/
│           │   └── ...
│           └── ...
```

## Physics Configuration

All job scripts automatically disable the following processes to prevent particle decay:
- **Muons (mu-, mu+)**: Process 1 (Decay), Process 7 (muMinusCaptureAtRest for mu-)
- **Pions (pi+, pi-)**: Process 1 (Decay)

To see all available processes for a particle, run:
```bash
./build/PhotonSim macros/list_processes.mac
```

## Workflow Examples

### Example 1: Monoenergetic Averaged Data (Large Statistics)
For generating lookup tables with high statistics (10k events) and averaged photon data:

```bash
# Use existing config or create one
./submit_photonsim_batch.sh -c muons_100_2000_10k.txt -s
```

### Example 2: Event-by-Event Fixed Energy
For studying individual events at a specific energy (e.g., 1050 MeV):

```bash
# Prepare and submit 100 jobs with 100 events each
./submit_photonsim_batch_individual.sh -c muons_1050_100jobs_100events.txt -s

# Monitor
./monitor_jobs.sh -w -o /sdf/data/neutrino/cjesus/photonsim_output/water/monoenergetic/event_by_event
```

### Example 3: Uniform Energy Distribution
For sampling across an energy range with individual photon information:

```bash
# Generate config for 100 muon jobs
./generate_uniform_energy_config.sh -p mu- -n 100

# Prepare and submit
./submit_photonsim_batch_uniform.sh -c muon_uniform_210_1500_MeV_100jobs_100events.txt -s

# Monitor
./monitor_jobs.sh -w -o /sdf/data/neutrino/cjesus/photonsim_output/water/uniform_energy

# Clean up temporary files after completion
./cleanup_jobs.sh -o /sdf/data/neutrino/cjesus/photonsim_output/water/uniform_energy -a
```

### Example 4: Pion Uniform Energy
```bash
# Generate config for 50 pion jobs with 200 events each
./generate_uniform_energy_config.sh -p pi+ -n 50 -e 200

# Submit
./submit_photonsim_batch_uniform.sh -c pion_plus_uniform_262_1500_MeV_50jobs_200events.txt -s
```

### Example 5: PhotonSim + LUCiD Pipeline
For generating both ROOT files and LUCiD-processed HDF5 files in a single job:

```bash
# Generate config for 100 muon jobs
./generate_uniform_energy_config.sh -p mu- -n 100

# Prepare and submit with LUCiD processing
./submit_photonsim_lucid_batch_uniform.sh -c muon_uniform_210_1500_MeV_100jobs_100events.txt -s

# Monitor
./monitor_jobs.sh -w -o /sdf/data/neutrino/cjesus/photonsim_output/water/uniform_energy

# Output will include both:
#   - output_jobXXX.root (PhotonSim)
#   - events_jobXXX.h5 (LUCiD)
```

**Custom LUCiD Path**:
```bash
./submit_photonsim_lucid_batch_uniform.sh -c config.txt -l /custom/path/to/LUCiD -s
```

## SLURM Configuration

Default SLURM settings (configured in `../user_paths.sh`):
- Partition: `shared`
- Account: `neutrino:cider-ml`
- CPUs: 1
- Memory: 4GB per CPU
- Time limit: 2 hours

Modify `user_paths.sh` to change these defaults.

## Quick Reference: Which Script to Use?

| Use Case | Energy | Individual Photons | Output Format | Script to Use | Config Generator |
|----------|--------|-------------------|---------------|---------------|------------------|
| Lookup tables, high stats | Fixed | No | ROOT | `submit_photonsim_batch.sh` | Manual config |
| Event-by-event at fixed E | Fixed | Yes | ROOT | `submit_photonsim_batch_individual.sh` | Manual config |
| Scan energy range | Uniform random | Yes | ROOT | `submit_photonsim_batch_uniform.sh` | `generate_uniform_energy_config.sh` |
| Full pipeline with LUCiD | Uniform random | Yes | ROOT + HDF5 | `submit_photonsim_lucid_batch_uniform.sh` | `generate_uniform_energy_config.sh` |

## Available Configuration Files

- `muons_100_2000_10k.txt` - Muons from 100-2000 MeV (10 MeV steps), 10k events each, averaged data
- `muons_1050_100jobs_100events.txt` - 100 jobs at 1050 MeV, 100 events each, event-by-event
- Generated by `generate_uniform_energy_config.sh` - Uniform energy distributions for mu- and pi+