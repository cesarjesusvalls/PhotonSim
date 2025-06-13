#!/usr/bin/env python3
"""
PhotonSim Data Visualizer

Interactive 3D visualization tool for optical photon data from PhotonSim.
Displays photons in 3D space with detector geometry and allows navigation
between events.

Usage:
    python visualize_photons.py [root_file]

Requirements:
    - uproot (for ROOT file reading)
    - numpy
    - matplotlib
    - ipywidgets (for interactive controls)

Author: PhotonSim Project
"""

import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import argparse
import sys
try:
    import uproot
except ImportError:
    print("Error: uproot package required. Install with: pip install uproot")
    sys.exit(1)

try:
    from ipywidgets import interact, IntSlider, Button, VBox, HBox, Output
    from IPython.display import display, clear_output
    JUPYTER_AVAILABLE = True
except ImportError:
    JUPYTER_AVAILABLE = False
    print("Note: ipywidgets not available. Using basic matplotlib interface.")


class PhotonSimVisualizer:
    """Interactive 3D visualizer for PhotonSim optical photon data."""
    
    def __init__(self, root_file_path):
        """
        Initialize the visualizer with ROOT file data.
        
        Args:
            root_file_path (str): Path to the ROOT file containing optical photon data
        """
        self.root_file_path = root_file_path
        self.data = None
        self.current_event = 0
        self.n_events = 0
        self.detector_size = 5.0  # Default 5m detector (will be updated from data)
        
        # Load data
        self.load_data()
        
        # Setup plot
        self.fig = None
        self.ax = None
        self.setup_plot()
    
    def load_data(self):
        """Load optical photon data from ROOT file."""
        try:
            with uproot.open(self.root_file_path) as file:
                tree = file["OpticalPhotons"]
                
                # Load all data arrays
                self.data = {
                    'EventID': tree['EventID'].array(library='np'),
                    'PrimaryEnergy': tree['PrimaryEnergy'].array(library='np'),
                    'NOpticalPhotons': tree['NOpticalPhotons'].array(library='np'),
                    'PhotonPosX': tree['PhotonPosX'].array(library='np'),
                    'PhotonPosY': tree['PhotonPosY'].array(library='np'),
                    'PhotonPosZ': tree['PhotonPosZ'].array(library='np'),
                    'PhotonDirX': tree['PhotonDirX'].array(library='np'),
                    'PhotonDirY': tree['PhotonDirY'].array(library='np'),
                    'PhotonDirZ': tree['PhotonDirZ'].array(library='np'),
                    'PhotonTime': tree['PhotonTime'].array(library='np'),
                }
                
                self.n_events = len(self.data['EventID'])
                print(f"Loaded {self.n_events} events from {self.root_file_path}")
                
                # Print summary statistics
                total_photons = np.sum(self.data['NOpticalPhotons'])
                avg_energy = np.mean(self.data['PrimaryEnergy'])
                print(f"Total optical photons: {total_photons:,}")
                print(f"Average primary energy: {avg_energy:.1f} MeV")
                
                # Estimate detector size from photon positions
                if self.n_events > 0:
                    all_x = np.concatenate(self.data['PhotonPosX'])
                    all_y = np.concatenate(self.data['PhotonPosY'])
                    all_z = np.concatenate(self.data['PhotonPosZ'])
                    
                    # Convert from mm to m and find detector bounds
                    max_extent = max(np.max(np.abs(all_x)), np.max(np.abs(all_y)), np.max(np.abs(all_z)))
                    self.detector_size = max_extent / 1000.0  # Convert mm to m
                    print(f"Estimated detector size: ±{self.detector_size:.1f} m")
                
        except Exception as e:
            print(f"Error loading ROOT file: {e}")
            sys.exit(1)
    
    def setup_plot(self):
        """Setup the 3D matplotlib figure."""
        plt.style.use('dark_background')
        self.fig = plt.figure(figsize=(12, 10))
        self.ax = self.fig.add_subplot(111, projection='3d')
        
        # Set up the plot aesthetics
        self.ax.set_facecolor('black')
        self.fig.patch.set_facecolor('black')
    
    def draw_detector_geometry(self):
        """Draw the detector volume outline."""
        # Define detector cube vertices (±detector_size in meters)
        size = self.detector_size
        vertices = np.array([
            [-size, -size, -size], [size, -size, -size], [size, size, -size], [-size, size, -size],  # bottom face
            [-size, -size, size], [size, -size, size], [size, size, size], [-size, size, size]      # top face
        ])
        
        # Define the edges of the cube
        edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # bottom face
            [4, 5], [5, 6], [6, 7], [7, 4],  # top face
            [0, 4], [1, 5], [2, 6], [3, 7]   # vertical edges
        ]
        
        # Draw the edges
        for edge in edges:
            points = vertices[edge]
            self.ax.plot3D(points[:, 0], points[:, 1], points[:, 2], 
                          color='cyan', alpha=0.3, linewidth=1)
    
    def get_event_data(self, event_id):
        """
        Get photon data for a specific event.
        
        Args:
            event_id (int): Event ID to retrieve
            
        Returns:
            dict: Event data including positions, directions, times
        """
        if event_id >= self.n_events:
            return None
            
        return {
            'event_id': self.data['EventID'][event_id],
            'primary_energy': self.data['PrimaryEnergy'][event_id],
            'n_photons': self.data['NOpticalPhotons'][event_id],
            'pos_x': self.data['PhotonPosX'][event_id] / 1000.0,  # Convert mm to m
            'pos_y': self.data['PhotonPosY'][event_id] / 1000.0,  # Convert mm to m
            'pos_z': self.data['PhotonPosZ'][event_id] / 1000.0,  # Convert mm to m
            'dir_x': self.data['PhotonDirX'][event_id],
            'dir_y': self.data['PhotonDirY'][event_id],
            'dir_z': self.data['PhotonDirZ'][event_id],
            'time': self.data['PhotonTime'][event_id],  # ns
        }
    
    def plot_event(self, event_id=None):
        """
        Plot optical photons for a specific event.
        
        Args:
            event_id (int): Event ID to plot. If None, uses current_event.
        """
        if event_id is None:
            event_id = self.current_event
            
        # Clear the plot
        self.ax.clear()
        
        # Get event data
        event_data = self.get_event_data(event_id)
        if event_data is None:
            print(f"Event {event_id} not found")
            return
        
        # Draw detector geometry
        self.draw_detector_geometry()
        
        # Plot photon positions
        n_photons = len(event_data['pos_x'])
        if n_photons > 0:
            # Color photons by creation time
            times = event_data['time']
            
            if np.max(times) > 0:
                # Normalize times for color mapping
                normalized_times = times / np.max(times)
                scatter = self.ax.scatter(event_data['pos_x'], event_data['pos_y'], event_data['pos_z'],
                                        c=normalized_times, s=1, alpha=0.6, cmap='plasma')
            else:
                # All times are zero, use uniform color
                scatter = self.ax.scatter(event_data['pos_x'], event_data['pos_y'], event_data['pos_z'],
                                        c='yellow', s=1, alpha=0.6)
            
            # Add some photon direction vectors (sample to avoid overcrowding)
            n_arrows = min(500, n_photons)  # Limit number of arrows
            indices = np.random.choice(n_photons, n_arrows, replace=False)
            
            arrow_scale = 0.2  # Scale factor for arrow length
            for i in indices:
                self.ax.quiver(event_data['pos_x'][i], event_data['pos_y'][i], event_data['pos_z'][i],
                              event_data['dir_x'][i] * arrow_scale,
                              event_data['dir_y'][i] * arrow_scale,
                              event_data['dir_z'][i] * arrow_scale,
                              color='white', alpha=0.3, arrow_length_ratio=0.1)
        
        # Plot primary particle origin
        self.ax.scatter([0], [0], [0], color='red', s=100, marker='*', 
                       label='Primary particle origin')
        
        # Set labels and title
        self.ax.set_xlabel('X [m]', color='white')
        self.ax.set_ylabel('Y [m]', color='white')
        self.ax.set_zlabel('Z [m]', color='white')
        
        # Set equal aspect ratio
        max_range = self.detector_size * 1.1
        self.ax.set_xlim([-max_range, max_range])
        self.ax.set_ylim([-max_range, max_range])
        self.ax.set_zlim([-max_range, max_range])
        
        # Title with event information
        title = f"Event {event_data['event_id']}: {event_data['primary_energy']:.1f} MeV electron\n"
        title += f"{event_data['n_photons']:,} Cherenkov photons"
        self.ax.set_title(title, color='white', fontsize=12)
        
        # Add colorbar for time
        if n_photons > 0 and np.max(times) > 0:
            cbar = plt.colorbar(scatter, ax=self.ax, shrink=0.6, aspect=20)
            cbar.set_label('Creation Time [ns]', color='white')
            cbar.ax.yaxis.set_tick_params(color='white')
            cbar.ax.yaxis.label.set_color('white')
        
        # Style the plot
        self.ax.tick_params(axis='x', colors='white')
        self.ax.tick_params(axis='y', colors='white')
        self.ax.tick_params(axis='z', colors='white')
        
        plt.tight_layout()
    
    def next_event(self):
        """Navigate to the next event."""
        if self.current_event < self.n_events - 1:
            self.current_event += 1
            self.plot_event()
            plt.draw()
    
    def previous_event(self):
        """Navigate to the previous event."""
        if self.current_event > 0:
            self.current_event -= 1
            self.plot_event()
            plt.draw()
    
    def goto_event(self, event_id):
        """
        Navigate to a specific event.
        
        Args:
            event_id (int): Event ID to navigate to
        """
        if 0 <= event_id < self.n_events:
            self.current_event = event_id
            self.plot_event()
            plt.draw()
    
    def create_interactive_plot(self):
        """Create interactive plot with navigation controls."""
        if JUPYTER_AVAILABLE:
            self._create_jupyter_interface()
        else:
            self._create_matplotlib_interface()
    
    def _create_matplotlib_interface(self):
        """Create matplotlib-based interface with keyboard controls."""
        def on_key(event):
            if event.key == 'right' or event.key == 'n':
                self.next_event()
            elif event.key == 'left' or event.key == 'p':
                self.previous_event()
            elif event.key == 'r':
                self.plot_event()  # Refresh
        
        self.fig.canvas.mpl_connect('key_press_event', on_key)
        
        # Plot initial event
        self.plot_event()
        
        # Add instructions
        self.fig.suptitle("Use arrow keys or 'n'/'p' to navigate events, 'r' to refresh", 
                         color='white', y=0.02)
        
        plt.show()
    
    def _create_jupyter_interface(self):
        """Create Jupyter notebook interface with widgets."""
        # Event slider
        event_slider = IntSlider(
            value=0, min=0, max=self.n_events-1,
            description='Event:', style={'description_width': 'initial'}
        )
        
        # Navigation buttons
        prev_button = Button(description='Previous')
        next_button = Button(description='Next')
        
        # Output widget for plot
        output = Output()
        
        def update_plot(event_id):
            with output:
                clear_output(wait=True)
                self.goto_event(event_id)
                plt.show()
        
        def on_slider_change(change):
            update_plot(change['new'])
        
        def on_prev_click(b):
            if event_slider.value > 0:
                event_slider.value -= 1
        
        def on_next_click(b):
            if event_slider.value < self.n_events - 1:
                event_slider.value += 1
        
        # Connect events
        event_slider.observe(on_slider_change, names='value')
        prev_button.on_click(on_prev_click)
        next_button.on_click(on_next_click)
        
        # Layout
        controls = HBox([prev_button, event_slider, next_button])
        interface = VBox([controls, output])
        
        # Initial plot
        with output:
            self.plot_event()
            plt.show()
        
        display(interface)


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Visualize PhotonSim optical photon data')
    parser.add_argument('root_file', nargs='?', default='optical_photons.root',
                       help='Path to ROOT file (default: optical_photons.root)')
    parser.add_argument('--event', type=int, default=0,
                       help='Initial event to display (default: 0)')
    
    args = parser.parse_args()
    
    # Check if file exists
    import os
    if not os.path.exists(args.root_file):
        print(f"Error: ROOT file '{args.root_file}' not found")
        sys.exit(1)
    
    # Create visualizer
    print(f"Creating PhotonSim visualizer for {args.root_file}")
    visualizer = PhotonSimVisualizer(args.root_file)
    
    # Set initial event
    if args.event < visualizer.n_events:
        visualizer.current_event = args.event
    
    # Create interactive plot
    visualizer.create_interactive_plot()


if __name__ == "__main__":
    main()