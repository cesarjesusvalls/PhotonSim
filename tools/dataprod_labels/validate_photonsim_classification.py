#!/usr/bin/env python3
"""
Generic validation script for PhotonSim label classification (no rotation).
Shows photons and tracks for each label in un-rotated events.
Creates interactive HTML plots for visual inspection.

Works with any particle type and any number of primaries.
"""
import sys
sys.path.append('/Users/cjesus/Software/LUCiD')

import os
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from tools.generate import read_label_data_from_photonsim
import argparse

def create_cylinder(start, end, radius, n_segments=16):
    """
    Create a 3D cylinder mesh between two points.

    Args:
        start: Starting point [x, y, z]
        end: Ending point [x, y, z]
        radius: Cylinder radius in world coordinates (cm)
        n_segments: Number of segments around the cylinder

    Returns:
        x, y, z: Arrays of vertex coordinates
        i, j, k: Arrays defining triangular faces
    """
    start = np.array(start)
    end = np.array(end)

    # Direction vector and length
    direction = end - start
    length = np.linalg.norm(direction)
    direction = direction / length

    # Find perpendicular vectors to create cylinder cross-section
    # Choose a vector not parallel to direction
    if abs(direction[0]) < 0.9:
        perp1 = np.cross(direction, [1, 0, 0])
    else:
        perp1 = np.cross(direction, [0, 1, 0])
    perp1 = perp1 / np.linalg.norm(perp1)
    perp2 = np.cross(direction, perp1)
    perp2 = perp2 / np.linalg.norm(perp2)

    # Create vertices
    vertices = []
    angles = np.linspace(0, 2*np.pi, n_segments, endpoint=False)

    # Bottom circle
    for angle in angles:
        point = start + radius * (np.cos(angle) * perp1 + np.sin(angle) * perp2)
        vertices.append(point)

    # Top circle
    for angle in angles:
        point = end + radius * (np.cos(angle) * perp1 + np.sin(angle) * perp2)
        vertices.append(point)

    vertices = np.array(vertices)
    x, y, z = vertices[:, 0], vertices[:, 1], vertices[:, 2]

    # Create triangular faces for the cylinder surface
    i, j, k = [], [], []
    for seg in range(n_segments):
        next_seg = (seg + 1) % n_segments

        # Two triangles per rectangular face
        # Triangle 1
        i.append(seg)
        j.append(next_seg)
        k.append(seg + n_segments)

        # Triangle 2
        i.append(next_seg)
        j.append(next_seg + n_segments)
        k.append(seg + n_segments)

    return x, y, z, i, j, k

# Parse command line arguments
parser = argparse.ArgumentParser(description='Validate PhotonSim label classification')
parser.add_argument('root_file', type=str, help='Input ROOT file from PhotonSim')
parser.add_argument('--events', type=int, default=50, help='Number of events to validate (default: 50)')
parser.add_argument('--photons', type=int, default=500, help='Number of photons to sample per label (default: 500)')
parser.add_argument('--seed', type=int, default=42, help='Random seed for photon sampling (default: 42)')
args = parser.parse_args()

root_file = args.root_file
events_to_validate = list(range(args.events))
n_photons_to_sample = args.photons
master_seed = args.seed

print("="*70)
print(f"PHOTONSIM LABEL CLASSIFICATION VALIDATION")
print("="*70)
print(f"Input file: {root_file}")
print(f"Events to validate: {args.events}")
print(f"Photons to sample per label: {n_photons_to_sample}")
print()

# Define colors for labels
colors_palette = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow',
                  'brown', 'pink', 'olive', 'navy', 'teal', 'maroon']
category_names = {0: 'Primary', 1: 'DecayElectron', 2: 'SecondaryPion', 3: 'GammaShower'}

# PDG code to particle name mapping
pdg_to_name = {
    -211: 'pi-',
    211: 'pi+',
    111: 'pi0',
    -13: 'mu+',
    13: 'mu-',
    -11: 'e+',
    11: 'e-',
    22: 'gamma',
    2212: 'proton',
    2112: 'neutron',
    -2212: 'antiproton',
}

# Statistics tracking by category
total_events = 0
category_counts = {0: 0, 1: 0, 2: 0, 3: 0}  # Primary, DecayElectron, SecondaryPion, GammaShower
events_with_category = {0: 0, 1: 0, 2: 0, 3: 0}
primary_particles = set()  # Track unique primary particle types

def process_event(event_idx):
    """Process a single event and return data for plotting"""
    global total_events, category_counts, events_with_category, primary_particles

    total_events += 1

    print(f"\n{'='*70}")
    print(f"EVENT {event_idx}")
    print(f"{'='*70}")

    # Read label data
    label_data = read_label_data_from_photonsim(root_file, event_idx)

    n_labels = label_data['n_labels']
    labels = label_data['labels']
    all_photon_origins = label_data['photon_origins']
    all_photon_directions = label_data['photon_directions']

    print(f"Event has {n_labels} labels")
    print()

    # Sample photons for each label
    sampled_photons = []
    sampled_directions = []
    track_positions = []
    track_directions = []
    label_colors = []
    label_names = []
    label_categories = []

    local_category_counts = {0: 0, 1: 0, 2: 0, 3: 0}

    for label_idx, label in enumerate(labels):
        photon_indices = label['photon_indices']
        track_info = label['track_info']

        if track_info is None:
            continue

        cat_name = category_names.get(track_info['category'], f"Unknown_{track_info['category']}")
        particle_name = pdg_to_name.get(track_info['pdg'], f"PDG{track_info['pdg']}")
        color = colors_palette[label_idx % len(colors_palette)]

        # Get kinetic energy (works for all particles)
        kinetic_energy = track_info['energy']  # MeV

        # Update statistics
        category = track_info['category']
        if category in category_counts:
            category_counts[category] += 1
            local_category_counts[category] += 1

        # Track primary particle types
        if category == 0:  # Primary
            primary_particles.add(particle_name)

        print(f"Label {label_idx} ({cat_name}):")
        print(f"  Particle: {particle_name} (PDG: {track_info['pdg']})")
        print(f"  Kinetic Energy: {kinetic_energy:.2f} MeV")
        print(f"  Color: {color}")
        print(f"  Track position: {track_info['position']}")
        print(f"  Track direction: {track_info['direction']}")
        print(f"  Total photons: {len(photon_indices)}")

        if len(photon_indices) == 0:
            print(f"  WARNING: No photons for this label")
            print()
            continue

        # Sample photons
        photon_indices_array = np.array(photon_indices, dtype=np.int32)
        n_to_sample = min(n_photons_to_sample, len(photon_indices))
        np.random.seed(master_seed + label_idx + event_idx * 100)
        sampled_indices = np.random.choice(len(photon_indices), size=n_to_sample, replace=False)
        selected_photon_indices = photon_indices_array[sampled_indices]

        photon_origins = all_photon_origins[selected_photon_indices]
        photon_dirs = all_photon_directions[selected_photon_indices]

        sampled_photons.append(photon_origins)
        sampled_directions.append(photon_dirs)
        track_positions.append(track_info['position'])
        track_directions.append(track_info['direction'])
        label_colors.append(color)

        # Create label name with kinetic energy
        label_name = f"Label {label_idx} ({cat_name} - {particle_name}, {kinetic_energy:.1f} MeV)"
        label_names.append(label_name)
        label_categories.append(track_info['category'])

        print(f"  Sampled {n_to_sample} photons")
        print()

    # Update events with category counts
    for cat, count in local_category_counts.items():
        if count > 0:
            events_with_category[cat] += 1

    print()

    return {
        'event_idx': event_idx,
        'n_labels': len(sampled_photons),
        'sampled_photons': sampled_photons,
        'track_positions': track_positions,
        'track_directions': track_directions,
        'label_colors': label_colors,
        'label_names': label_names,
        'label_categories': label_categories
    }

# Process all events
events_data = []
for event_idx in events_to_validate:
    try:
        event_data = process_event(event_idx)
        if event_data is not None:
            events_data.append(event_data)
    except Exception as e:
        print(f"ERROR processing event {event_idx}: {e}")
        import traceback
        traceback.print_exc()
        continue

# Print summary statistics
print()
print("="*70)
print("CLASSIFICATION STATISTICS")
print("="*70)
print(f"Total events processed: {total_events}")
print()
print("Primary particle types detected:", ', '.join(sorted(primary_particles)))
print()
print("Category breakdown:")
for cat_id in sorted(category_counts.keys()):
    cat_name = category_names.get(cat_id, f"Unknown_{cat_id}")
    count = category_counts[cat_id]
    events_with = events_with_category[cat_id]
    if total_events > 0:
        avg_per_event = count / total_events
        pct_events = 100 * events_with / total_events
        print(f"  {cat_name:20s}: {count:4d} total | {events_with:3d} events ({pct_events:.1f}%) | {avg_per_event:.2f} per event")
print()

# Create interactive plots for all events
print()
print("="*70)
print("CREATING INTERACTIVE VISUALIZATIONS")
print("="*70)

events_to_plot = events_data
print(f"Creating plots for {len(events_to_plot)} events")
print()

for event_data in events_to_plot:
    event_idx = event_data['event_idx']

    # Create single plot
    fig = go.Figure()

    # Plot each label
    for i in range(event_data['n_labels']):
        photons = event_data['sampled_photons'][i]
        track_pos = event_data['track_positions'][i]
        track_dir = event_data['track_directions'][i]
        color = event_data['label_colors'][i]
        label_name = event_data['label_names'][i]
        category = event_data['label_categories'][i]

        # Plot photons
        fig.add_trace(
            go.Scatter3d(
                x=photons[:, 0], y=photons[:, 1], z=photons[:, 2],
                mode='markers',
                marker=dict(size=2, color=color, opacity=0.3),
                name=label_name,
                legendgroup=f'label{i}',
                showlegend=True
            )
        )

        # Plot track arrow for all categories
        scale = 20  # Arrow length in cm
        cylinder_radius = 1.5  # Cylinder radius in cm

        # Draw the cylinder (3D object with proper world-space thickness) - HIDDEN BY DEFAULT
        cylinder_end = track_pos + track_dir * scale
        cyl_x, cyl_y, cyl_z, cyl_i, cyl_j, cyl_k = create_cylinder(
            track_pos, cylinder_end, cylinder_radius
        )

        fig.add_trace(
            go.Mesh3d(
                x=cyl_x,
                y=cyl_y,
                z=cyl_z,
                i=cyl_i,
                j=cyl_j,
                k=cyl_k,
                color=color,
                opacity=1.0,
                name=f'{label_name} track',
                legendgroup=f'label{i}',
                showlegend=False,
                visible=False,  # Hidden by default
                lighting=dict(ambient=0.8, diffuse=0.8, specular=0.2),
                flatshading=False
            )
        )

        # Add cone arrowhead at the tip (bigger) - HIDDEN BY DEFAULT
        tip_x = track_pos[0] + track_dir[0]*scale
        tip_y = track_pos[1] + track_dir[1]*scale
        tip_z = track_pos[2] + track_dir[2]*scale

        fig.add_trace(
            go.Cone(
                x=[tip_x],
                y=[tip_y],
                z=[tip_z],
                u=[track_dir[0]],
                v=[track_dir[1]],
                w=[track_dir[2]],
                colorscale=[[0, color], [1, color]],
                sizemode="absolute",
                sizeref=20,
                showscale=False,
                name=f'{label_name} direction',
                legendgroup=f'label{i}',
                showlegend=False,
                visible=False  # Hidden by default
            )
        )

    # Create visibility arrays for toggle button
    # Each label has 3 traces: photons, arrow line, arrow cone
    n_traces = len(fig.data)

    # Show arrows: keep photons visible, show arrows
    show_arrows = []
    for i in range(n_traces):
        if i % 3 == 0:  # Photon traces
            show_arrows.append(True)
        else:  # Arrow traces (line and cone)
            show_arrows.append(True)

    # Hide arrows: keep photons visible, hide arrows
    hide_arrows = []
    for i in range(n_traces):
        if i % 3 == 0:  # Photon traces
            hide_arrows.append(True)
        else:  # Arrow traces (line and cone)
            hide_arrows.append(False)

    # Update layout with toggle button
    primary_desc = ', '.join(sorted(primary_particles)) if primary_particles else "Unknown"
    fig.update_layout(
        title=f'Event {event_idx}: PhotonSim Classification ({primary_desc})',
        scene=dict(
            xaxis_title='X (cm)',
            yaxis_title='Y (cm)',
            zaxis_title='Z (cm)',
            aspectmode='data'
        ),
        legend=dict(
            itemsizing='constant',
            itemwidth=50,
            tracegroupgap=5,
            font=dict(size=12)
        ),
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=[
                    dict(
                        args=[{"visible": show_arrows}],
                        label="Show Arrows",
                        method="update"
                    ),
                    dict(
                        args=[{"visible": hide_arrows}],
                        label="Hide Arrows",
                        method="update"
                    )
                ],
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.0,
                xanchor="left",
                y=1.08,
                yanchor="top"
            ),
        ],
        height=700,
        width=1000
    )

    # Save as HTML with root file basename to avoid overwriting
    root_basename = os.path.splitext(os.path.basename(root_file))[0]
    filename = f'{root_basename}_event{event_idx}.html'
    fig.write_html(filename)
    print(f"✓ Saved event {event_idx} to {filename}")

print()
print("="*70)
print("VALIDATION COMPLETE")
print("="*70)
print(f"\nGenerated {len(events_to_plot)} HTML files")
print("Open the HTML files in a browser to interactively explore the 3D plots")
