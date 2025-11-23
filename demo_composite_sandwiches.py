"""
Demonstration script showing composite facesheet sandwich panel capabilities.

Run this to see a comparison of aluminum vs composite sandwich panels.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models.material import PredefinedMaterials


def print_separator():
    print("\n" + "=" * 80 + "\n")


def format_number(value, decimals=2):
    """Format number with scientific notation if needed."""
    if abs(value) >= 1000 or abs(value) < 0.01:
        return f"{value:.{decimals}e}"
    else:
        return f"{value:.{decimals}f}"


def print_sandwich_comparison():
    """Compare aluminum and composite sandwich panels."""
    print_separator()
    print("SANDWICH PANEL COMPARISON: ALUMINUM vs COMPOSITE")
    print_separator()

    # Create sandwich panels
    al_sandwich = PredefinedMaterials.create_aluminum_sandwich()
    comp_sandwich = PredefinedMaterials.create_composite_sandwich()
    comp_thick = PredefinedMaterials.create_composite_sandwich_thick()

    sandwiches = [
        ("Aluminum 7050 Sandwich", al_sandwich),
        ("Carbon IM7/M91 Composite", comp_sandwich),
        ("Carbon AS4c/M21 Thick", comp_thick)
    ]

    for name, sandwich in sandwiches:
        props = sandwich.get_equivalent_properties()

        print(f"{name}")
        print("-" * 80)
        print(f"  Face Material Type: {type(sandwich.face_material).__name__}")
        print(f"  Face Material: {sandwich.face_material.name}")
        print(f"  Face Thickness: {sandwich.face_thickness:.3f} mm")
        print(f"  Core Material: {sandwich.core_material.name}")
        print(f"  Core Thickness: {sandwich.core_thickness:.1f} mm")
        print(f"  Total Thickness: {sandwich.total_thickness:.3f} mm")
        print()
        print(f"  Face Modulus (E): {props['face_youngs']/1e9:.1f} GPa")
        print(f"  Face Poisson (nu): {props['face_poisson']:.3f}")
        print(f"  Core Shear (G): {props['core_shear']/1e6:.1f} MPa")
        print()
        print(f"  Mass per Area: {props['mass_per_area']:.4f} kg/m^2")
        print(f"  Flexural Rigidity (D): {format_number(props['flexural_rigidity'], 3)} N*m")
        print(f"  Effective E: {props['effective_youngs_modulus']/1e9:.1f} GPa")
        print(f"  Weight Saving vs Solid: {props['weight_saving']:.1f}%")
        print(f"  Equiv. Solid Thickness: {props['equivalent_solid_thickness_m']*1000:.3f} mm")
        print(f"  First Mode Freq (508x254mm): ~{props['first_mode_freq_estimate']:.1f} Hz")
        print()

    # Calculate performance ratios
    al_props = al_sandwich.get_equivalent_properties()
    comp_props = comp_sandwich.get_equivalent_properties()

    print_separator()
    print("PERFORMANCE COMPARISON: COMPOSITE vs ALUMINUM")
    print_separator()

    weight_saving = (1 - comp_props['mass_per_area'] / al_props['mass_per_area']) * 100
    stiffness_ratio = comp_props['flexural_rigidity'] / al_props['flexural_rigidity']
    thickness_ratio = comp_sandwich.face_thickness / al_sandwich.face_thickness
    specific_stiffness_ratio = (comp_props['flexural_rigidity'] / comp_props['mass_per_area']) / \
                                (al_props['flexural_rigidity'] / al_props['mass_per_area'])

    print(f"Weight Saving: {weight_saving:.1f}%")
    print(f"  - Aluminum mass: {al_props['mass_per_area']:.4f} kg/m^2")
    print(f"  - Composite mass: {comp_props['mass_per_area']:.4f} kg/m^2")
    print()

    print(f"Stiffness Ratio: {stiffness_ratio:.2f}x")
    print(f"  - Aluminum D: {format_number(al_props['flexural_rigidity'], 3)} N*m")
    print(f"  - Composite D: {format_number(comp_props['flexural_rigidity'], 3)} N*m")
    print(f"  - Note: Composite uses thinner facesheets ({thickness_ratio:.2f}x)")
    print()

    print(f"Specific Stiffness (D/m) Ratio: {specific_stiffness_ratio:.2f}x")
    print(f"  - This is the key metric: stiffness per unit mass")
    print(f"  - Composite has {specific_stiffness_ratio:.2f}x better stiffness-to-weight!")
    print()

    # Flutter implications
    flutter_ratio = (comp_props['first_mode_freq_estimate'] /
                     al_props['first_mode_freq_estimate'])

    print(f"First Mode Frequency Ratio: {flutter_ratio:.2f}x")
    print(f"  - Aluminum: ~{al_props['first_mode_freq_estimate']:.1f} Hz")
    print(f"  - Composite: ~{comp_props['first_mode_freq_estimate']:.1f} Hz")
    print(f"  - Higher frequency -> Better flutter margin")
    print()

    print_separator()
    print("FIGHTER AIRCRAFT APPLICATIONS")
    print_separator()

    applications = [
        ("F/A-18 Wing Skin", "IM7/M91", "0.194-0.388", "60-70%", "Stealth + weight savings"),
        ("F-16 Access Panel", "AS4c/M21", "0.285-0.57", "40-50%", "Impact resistance"),
        ("Radome Panel", "Quartz/8552", "0.285-0.57", "30-40%", "RF transparency"),
        ("Eurofighter Skin", "IM7/M91", "0.388-0.776", "65-75%", "High stiffness")
    ]

    print(f"{'Application':<25} {'Material':<15} {'Thick (mm)':<15} {'Wt Save':<10} {'Benefit'}")
    print("-" * 100)
    for app, mat, thick, save, benefit in applications:
        print(f"{app:<25} {mat:<15} {thick:<15} {save:<10} {benefit}")

    print()
    print("All these applications are NOW SUPPORTED in the GUI!")

    print_separator()
    print("MATERIAL SELECTION GUIDE")
    print_separator()

    print("Choose ALUMINUM facesheets when:")
    print("  + Impact resistance is critical")
    print("  + Manufacturing cost must be minimized")
    print("  + Electrical conductivity required (lightning protection)")
    print("  + Repair simplicity is important")
    print()

    print("Choose COMPOSITE facesheets when:")
    print("  + Weight savings is critical (60-70% reduction)")
    print("  + High specific stiffness needed")
    print("  + Radar cross-section reduction required (stealth)")
    print("  + Fatigue resistance is important (no metal fatigue)")
    print("  + RF transparency needed (quartz fabric)")
    print()

    print("Trade-off: Composites cost 2-3x more but save 60-70% weight.")
    print("           For fighter aircraft, this trade is almost always worth it!")

    print_separator()


def print_custom_sandwich_example():
    """Show how to create custom composite sandwich."""
    print_separator()
    print("CUSTOM COMPOSITE SANDWICH EXAMPLE")
    print_separator()

    from models.material import SandwichPanel

    # Create custom sandwich with thick composite faces
    custom = SandwichPanel(
        id=100,
        name="Custom F-16 Wing Root Sandwich",
        face_material=PredefinedMaterials.as4c_m21(),  # Balanced fabric
        face_thickness=0.57,  # mm (2 plies x 285 g/m^2)
        core_material=PredefinedMaterials.aluminum_honeycomb_5056(),  # High density
        core_thickness=25.4,  # mm (1.0 inch)
        description="Custom heavy-duty sandwich for high bending loads"
    )

    props = custom.get_equivalent_properties()

    print("Configuration:")
    print(f"  Face: {custom.face_material.name} (orthotropic)")
    print(f"  Face Thickness: {custom.face_thickness} mm (2-ply layup)")
    print(f"  Core: {custom.core_material.name}")
    print(f"  Core Thickness: {custom.core_thickness} mm")
    print(f"  Total Thickness: {custom.total_thickness} mm")
    print()

    print("Performance:")
    print(f"  Mass: {props['mass_per_area']:.4f} kg/m^2")
    print(f"  Flexural Rigidity: {format_number(props['flexural_rigidity'], 3)} N*m")
    print(f"  Effective E: {props['effective_youngs_modulus']/1e9:.1f} GPa")
    print(f"  Weight Saving: {props['weight_saving']:.1f}%")
    print()

    print("Application: F-16 wing root panel with:")
    print("  - Very high bending loads (wing attachment)")
    print("  - 2-ply balanced fabric for impact resistance")
    print("  - High-density core for compression strength")
    print("  - Total weight: ~2.5 kg/m^2 vs 8.2 kg/m^2 aluminum equivalent")

    print_separator()


def main():
    """Run demonstration."""
    print()
    print("+" + "=" * 78 + "+")
    print("|" + " " * 78 + "|")
    print("|" + "  COMPOSITE FACESHEET SANDWICH PANEL DEMONSTRATION".center(78) + "|")
    print("|" + "  Panel Flutter Analysis Tool v2.2.1".center(78) + "|")
    print("|" + " " * 78 + "|")
    print("+" + "=" * 78 + "+")

    print_sandwich_comparison()
    print_custom_sandwich_example()

    print()
    print("[SUCCESS] All these configurations can now be created in the GUI!")
    print()
    print("To use in GUI:")
    print("  1. Run: python main.py")
    print("  2. Navigate to: Material Panel -> Sandwich Tab")
    print("  3. Select composite material from dropdown:")
    print("     - IM7/M91 (Carbon/Epoxy) - High modulus unidirectional")
    print("     - AS4c/M21 (Carbon Fabric) - Balanced fabric, impact resistant")
    print("     - Quartz/8552 (Quartz Fabric) - RF transparent for radomes")
    print("  4. Enter thicknesses and calculate properties")
    print("  5. Save to project for flutter analysis")
    print()
    print("For more information, see: COMPOSITE_FACESHEET_UPGRADE.md")
    print()


if __name__ == '__main__':
    main()
