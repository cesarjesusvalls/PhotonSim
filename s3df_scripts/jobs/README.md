# PhotonSim S3DF Job Scripts

This directory contains scripts for submitting and managing PhotonSim jobs on the S3DF cluster.

## Scripts Overview

### 1. submit_photonsim_job.sh
Submit a single PhotonSim job with specified parameters.

```bash
./submit_photonsim_job.sh -p <particle> -n <nevents> -e <energy> -o <output_dir> [-f <filename>]
```

Options:
- `-p`: Particle type (default: mu-)
- `-n`: Number of events (default: 1000)
- `-e`: Energy in MeV (default: 1000)
- `-o`: Output directory (required)
- `-f`: Output filename (default: output.root)

Example:
```bash
./submit_photonsim_job.sh -p mu- -n 10000 -e 1000 -o /sdf/data/neutrino/cjesus/photonsim_output
```

### 2. submit_photonsim_batch.sh
Submit multiple PhotonSim jobs from a configuration file.

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
./submit_photonsim_batch.sh -c example_batch_config.txt

# Prepare and submit all jobs
./submit_photonsim_batch.sh -c example_batch_config.txt -s

# Test with first job only
./submit_photonsim_batch.sh -c example_batch_config.txt -t
```

### 3. monitor_jobs.sh
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
./monitor_jobs.sh -w -o /sdf/data/neutrino/cjesus/photonsim_output
```

### 4. cleanup_jobs.sh
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
./cleanup_jobs.sh -o /sdf/data/neutrino/cjesus/photonsim_output -a

# Clean only log files
./cleanup_jobs.sh -o /sdf/data/neutrino/cjesus/photonsim_output -l
```

## Directory Structure

Jobs are organized following this convention:
```
output_directory/
├── particle_type/
│   ├── energyMeV/
│   │   ├── output.root              # Simulation output
│   │   ├── run_*.mac               # GEANT4 macro
│   │   ├── run_photonsim.sh       # Job execution script
│   │   ├── submit_job.sbatch      # SLURM submission script
│   │   ├── job-*.out              # SLURM output log
│   │   └── job-*.err              # SLURM error log
```

## Workflow Example

1. Create a configuration file:
```bash
cat > my_jobs.txt << EOF
mu- 1000 500 /sdf/data/neutrino/cjesus/photonsim_output
mu- 1000 1000 /sdf/data/neutrino/cjesus/photonsim_output
mu- 1000 2000 /sdf/data/neutrino/cjesus/photonsim_output
EOF
```

2. Prepare and submit jobs:
```bash
./submit_photonsim_batch.sh -c my_jobs.txt -s
```

3. Monitor progress:
```bash
./monitor_jobs.sh -w -o /sdf/data/neutrino/cjesus/photonsim_output
```

4. Clean up after completion:
```bash
./cleanup_jobs.sh -o /sdf/data/neutrino/cjesus/photonsim_output -a
```

## SLURM Configuration

Default SLURM settings in the scripts:
- Partition: `shared`
- Account: `neutrino:cider-ml`
- CPUs: 1
- Memory: 4GB per CPU
- Time limit: 2 hours

Modify the submit scripts if different resources are needed.