#!/usr/bin/env python3
"""
Validation script for pion classification (no rotation).
Shows photons and tracks for each label in un-rotated events.
Creates interactive HTML plots for visual inspection.
"""
import sys
sys.path.append('/Users/cjesus/Software/LUCiD')

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from tools.generate import read_label_data_from_photonsim

# Configuration
root_file = 'test_1pion.root'
events_to_validate = list(range(50))  # Validate 50 events
n_photons_to_sample = 500
master_seed = 42

# Get primary energy from first event
try:
    first_event_data = read_label_data_from_photonsim(root_file, 0)
    primary_energy = first_event_data.get('primary_energy', 500.0)
except:
    primary_energy = 500.0

print("="*70)
print(f"PION CLASSIFICATION VALIDATION ({primary_energy:.0f} MeV pi-)")
print("="*70)
print()

# Define colors for labels
colors_palette = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow']
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
}

# Statistics tracking
total_events = 0
events_with_secondary_pions = 0
total_secondary_pions = 0
total_gamma_showers = 0
total_decay_electrons = 0

def process_event(event_idx):
    """Process a single event and return data for plotting"""
    global total_events, events_with_secondary_pions, total_secondary_pions
    global total_gamma_showers, total_decay_electrons

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

    local_secondary_pions = 0

    for label_idx, label in enumerate(labels):
        photon_indices = label['photon_indices']
        track_info = label['track_info']

        if track_info is None:
            continue

        cat_name = category_names.get(track_info['category'], f"Unknown_{track_info['category']}")
        particle_name = pdg_to_name.get(track_info['pdg'], f"PDG{track_info['pdg']}")
        color = colors_palette[label_idx % len(colors_palette)]

        # Calculate momentum for pions (E_total² = (pc)² + (mc²)²)
        momentum = None
        if abs(track_info['pdg']) == 211:  # Charged pion
            pion_mass = 139.57  # MeV/c²
            kinetic_energy = track_info['energy']  # MeV (kinetic energy from GEANT4)
            total_energy = kinetic_energy + pion_mass  # Total energy
            momentum_sq = total_energy**2 - pion_mass**2
            if momentum_sq > 0:
                momentum = int(np.sqrt(momentum_sq))  # MeV/c, no decimals

        # Update statistics
        if track_info['category'] == 2:  # SecondaryPion
            local_secondary_pions += 1
            total_secondary_pions += 1
        elif track_info['category'] == 3:  # GammaShower
            total_gamma_showers += 1
        elif track_info['category'] == 1:  # DecayElectron
            total_decay_electrons += 1

        print(f"Label {label_idx} ({cat_name}):")
        print(f"  PDG: {track_info['pdg']}")
        print(f"  Energy: {track_info['energy']:.2f} MeV")
        if momentum is not None:
            print(f"  Momentum: {momentum} MeV/c")
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

        # Create label name with momentum for pions
        if momentum is not None:
            label_name = f"Label {label_idx} ({cat_name} - {particle_name}, {momentum} MeV/c)"
        else:
            label_name = f"Label {label_idx} ({cat_name} - {particle_name})"
        label_names.append(label_name)
        label_categories.append(track_info['category'])

        print(f"  Sampled {n_to_sample} photons")
        print()

    if local_secondary_pions > 0:
        events_with_secondary_pions += 1
        print(f"*** Event {event_idx} has {local_secondary_pions} secondary pion(s) ***")

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
        continue

# Print summary statistics
print()
print("="*70)
print("CLASSIFICATION STATISTICS")
print("="*70)
print(f"Total events processed: {total_events}")
print(f"Events with secondary pions: {events_with_secondary_pions} ({100*events_with_secondary_pions/total_events:.1f}%)")
print(f"Total secondary pions: {total_secondary_pions}")
print(f"Total gamma showers: {total_gamma_showers}")
print(f"Total decay electrons: {total_decay_electrons}")
print(f"Average secondary pions per event: {total_secondary_pions/total_events:.2f}")
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

        # Plot track arrow for all categories (now that gammas have proper directions)
        scale = 5  # Arrow length in cm (shorter)

        # Draw the line (thicker) - HIDDEN BY DEFAULT
        fig.add_trace(
            go.Scatter3d(
                x=[track_pos[0], track_pos[0] + track_dir[0]*scale],
                y=[track_pos[1], track_pos[1] + track_dir[1]*scale],
                z=[track_pos[2], track_pos[2] + track_dir[2]*scale],
                mode='lines',
                line=dict(color=color, width=12),
                name=f'{label_name} track',
                legendgroup=f'label{i}',
                showlegend=False,
                visible=False  # Hidden by default
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
                sizeref=4,
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
    fig.update_layout(
        title=f'Event {event_idx}: Pion Classification ({primary_energy:.0f} MeV pi-)',
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

    # Save as HTML
    filename = f'pion_classification_event{event_idx}.html'
    fig.write_html(filename)
    print(f"✓ Saved event {event_idx} to {filename}")

print()
print("="*70)
print("VALIDATION COMPLETE")
print("="*70)
print(f"\nGenerated {len(events_to_plot)} HTML files for events with secondary pions")
print("Open the HTML files in a browser to interactively explore the 3D plots")
