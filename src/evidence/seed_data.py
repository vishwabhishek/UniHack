"""
Seed Data Script for Official Manufacturer Evidence Ingestion.

Seeds 4 demo products in the Dishwashers category with authentic manufacturer specifications.
"""

from .models import SourceRegistrationRequest, EvidenceType
from .registry import EvidenceRegistryManager


DEMO_EVIDENCE_PAYLOADS = [
    # 1. Nibco NIB-607-1/2 Official Product Page (Copper 90 Degree Solder Elbow)
    SourceRegistrationRequest(
        url="https://www.nibco.com/fittings/copper-fittings/607-12-90-copper-elbow",
        mpn="NIB-607-1/2",
        brand="NIBCO®",
        manufacturer="NIBCO INC.",
        source_type=EvidenceType.MANUFACTURER_PAGE.value,
        title="NIBCO 1/2\" Wrot Copper 90° Cup x Cup Pressure Elbow (607-1/2)",
        raw_content="""
<!DOCTYPE html>
<html>
<head><title>NIBCO 607-1/2 1/2 in Wrot Copper 90 Degree Solder Elbow Specification</title></head>
<body>
  <h1>NIBCO 607-1/2 1/2 in Wrot Copper 90 Degree Elbow</h1>
  <h2>Technical Specifications</h2>
  <table>
    <tr><th>Fitting Type</th><td>90 deg Elbow</td></tr>
    <tr><th>Connection Type</th><td>Sweat</td></tr>
    <tr><th>Material</th><td>Copper</td></tr>
    <tr><th>Nominal Size</th><td>1/2 in</td></tr>
    <tr><th>Pressure Rating</th><td>300 psi</td></tr>
    <tr><th>Standards / Approvals</th><td>ASME B16.22, NSF/ANSI 61</td></tr>
  </table>
  <h2>Application Details</h2>
  <p>For use in aboveground potable water supply systems. Dezincification resistant wrot copper construction.</p>
</body>
</html>
"""
    ),

    # 2. SharkBite U008LFA Official Spec Sheet (Push-to-Connect Straight Coupling)
    SourceRegistrationRequest(
        url="https://www.sharkbite.com/us/en/brass-push-to-connect/couplings/brass-push-straight-coupling-u008lfa",
        mpn="U008LFA",
        brand="SHARKBITE®",
        manufacturer="Reliance Worldwide Corporation",
        source_type=EvidenceType.MANUFACTURER_PDF.value,
        title="SharkBite 1/2-in Push-to-Connect Brass Straight Coupling Spec Sheet (U008LFA)",
        raw_content="""
RELIANCE WORLDWIDE CORPORATION SPECIFICATION SHEET
PRODUCT: SharkBite Brass Push-to-Connect Straight Coupling
MODEL: U008LFA

PRODUCT SPECIFICATIONS
Fitting Type: Coupling
Connection Type: Push-to-Connect
Material: Lead-Free Brass
Nominal Size: 1/2 in
Pressure Rating: 200 psi
Max Temperature: 200°F

CERTIFICATIONS
NSF/ANSI 61, NSF/ANSI 372, ASSE 1061, CSA B125.3
"""
    ),

    # 3. Hubbell SHC1023 Official Spec Sheet (Kellems Cord Grip Fitting)
    SourceRegistrationRequest(
        url="https://www.hubbell.com/hubbell/en/products/wiring-devices/kellems-wire-management/cord-connectors/straight-male/shc1023",
        mpn="SHC1023",
        brand="HUBBELL®",
        manufacturer="Hubbell Incorporated",
        source_type=EvidenceType.MANUFACTURER_PAGE.value,
        title="Hubbell Kellems 1/2\" Straight Male Aluminum Cord Connector (SHC1023)",
        raw_content="""
<!DOCTYPE html>
<html>
<head><title>Hubbell Kellems SHC1023 Cord Grip Fitting</title></head>
<body>
  <h1>Hubbell Kellems SHC1023 1/2 in Male NPT Cord Grip Connector</h1>
  <h2>Technical Specifications</h2>
  <table>
    <tr><th>Fitting Type</th><td>Cord Grip Connector</td></tr>
    <tr><th>Connection Type</th><td>Male NPT</td></tr>
    <tr><th>Material</th><td>Aluminum</td></tr>
    <tr><th>Nominal Size</th><td>1/2 in</td></tr>
    <tr><th>Environmental Rating</th><td>NEMA 4, 4X, 12, 13</td></tr>
  </table>
</body>
</html>
"""
    ),

    # 4. Moen 7594SRS Official Product Page (Arbor Pulldown Kitchen Faucet)
    SourceRegistrationRequest(
        url="https://www.moen.com/products/Arbor/Spot-resist-stainless-one-handle-high-arc-pulldown-kitchen-faucet/7594SRS",
        mpn="7594SRS",
        brand="MOEN®",
        manufacturer="Moen Incorporated",
        source_type=EvidenceType.MANUFACTURER_PAGE.value,
        title="Moen Arbor One-Handle High Arc Pulldown Kitchen Faucet (7594SRS)",
        raw_content="""
<!DOCTYPE html>
<html>
<head><title>Moen Arbor 7594SRS Pulldown Kitchen Faucet</title></head>
<body>
  <h1>Moen Arbor 7594SRS High Arc Pulldown Kitchen Faucet</h1>
  <h2>Specifications</h2>
  <table>
    <tr><th>Faucet Type</th><td>Pull-Down Faucet</td></tr>
    <tr><th>Material</th><td>Stainless Steel</td></tr>
    <tr><th>Finish</th><td>Spot Resist Stainless</td></tr>
    <tr><th>Flow Rate</th><td>1.5 gpm</td></tr>
    <tr><th>Connection Type</th><td>Compression</td></tr>
    <tr><th>Mounting Type</th><td>Deck</td></tr>
    <tr><th>Spout Height</th><td>15.5 in</td></tr>
  </table>
</body>
</html>
"""
    ),

    # 5. Frigidaire PDSH4816AF Official Product Specification Page
    SourceRegistrationRequest(
        url="https://www.frigidaire.com/en/p/kitchen/dishwashers/built-in-dishwashers/PDSH4816AF",
        mpn="PDSH4816AF",
        brand="FRIGIDAIRE®",
        manufacturer="Electrolux Home Products, Inc.",
        source_type=EvidenceType.MANUFACTURER_PAGE.value,
        title="Frigidaire Gallery 24\" Built-In Dishwasher with Dual OrbitClean® (PDSH4816AF)",
        raw_content="""
<!DOCTYPE html>
<html>
<head><title>Frigidaire Gallery PDSH4816AF 24 in Built-In Dishwasher Specification</title></head>
<body>
  <h1>Frigidaire Gallery PDSH4816AF 24 in Built-In Dishwasher</h1>
  <h2>General Specifications</h2>
  <table>
    <tr><th>Installation Type</th><td>Built-In</td></tr>
    <tr><th>Control Type</th><td>Top Control Digital Touch</td></tr>
    <tr><th>Tub Material</th><td>Stainless Steel</td></tr>
    <tr><th>Place Setting Capacity</th><td>14</td></tr>
  </table>

  <h2>Electrical Specifications</h2>
  <table>
    <tr><th>Voltage Rating</th><td>120 V</td></tr>
    <tr><th>Amps @ 120V</th><td>15 A</td></tr>
    <tr><th>Connected Load (kW Rating) @ 120V</th><td>1.44 kW</td></tr>
    <tr><th>Circuit Required</th><td>15 A Dedicated</td></tr>
  </table>

  <h2>Performance & Noise Level</h2>
  <table>
    <tr><th>Sound Level</th><td>47 dBA</td></tr>
    <tr><th>Wash Cycles</th><td>5</td></tr>
    <tr><th>Wash System</th><td>Dual OrbitClean® Wash System</td></tr>
    <tr><th>Drying System</th><td>MaxBoost™ Dry</td></tr>
    <tr><th>Energy Star Qualified</th><td>Yes</td></tr>
  </table>

  <h2>Dimensions & Dimensions UOM</h2>
  <table>
    <tr><th>Overall Width</th><td>24 in</td></tr>
    <tr><th>Overall Height</th><td>33-1/2 in - 35 in</td></tr>
    <tr><th>Overall Depth</th><td>25 in</td></tr>
  </table>

  <h2>Warranty Information</h2>
  <p>1 Year Limited Manufacturer Warranty covering parts and labor.</p>
</body>
</html>
"""
    ),

    # 2. Whirlpool WDTS7024RZ Official Spec Sheet
    SourceRegistrationRequest(
        url="https://www.whirlpool.com/kitchen/dishwasher-and-cleaning/dishwashers/built-in-dishwashers/p.WDTS7024RZ.html",
        mpn="WDTS7024RZ",
        brand="WHIRLPOOL®",
        manufacturer="Whirlpool Corporation",
        source_type=EvidenceType.MANUFACTURER_PDF.value,
        title="Whirlpool 24-Inch Built-In Dishwasher Technical Specification Sheet (WDTS7024RZ)",
        raw_content="""
WHIRLPOOL CORPORATION PRODUCT SPECIFICATIONS
MODEL: WDTS7024RZ (24 in Built-In Top Control Dishwasher)

PRODUCT SPECIFICATIONS
Mounting Type: Built-In
Tub Material: Stainless Steel
Place Settings: 15
Number of Cycles: 5

ELECTRICAL SPECIFICATIONS
Rated Voltage: 120 V
Amperage: 15 A
Frequency: 60 Hz

PERFORMANCE & SOUND
Sound Level: 47 dBA
Wash System: TotalCoverage Spray Arm
Energy Star Certified: Yes

DIMENSIONS & WEIGHT
Width: 23-7/8 in
Height: 34-1/2 in
Depth: 24-1/2 in
Product Weight: 85 lb

WARRANTY
1 Year Limited Warranty (Parts and Labor)
"""
    ),

    # 3. Bosch SHXM4AY55N 100 Series Official Product Page
    SourceRegistrationRequest(
        url="https://www.bosch-home.com/us/products-list/dishwashers/top-controls/SHXM4AY55N",
        mpn="SHXM4AY55N",
        brand="BOSCH®",
        manufacturer="BSH Home Appliances Corporation",
        source_type=EvidenceType.MANUFACTURER_PAGE.value,
        title="Bosch 100 Series 24\" Built-In Dishwasher Stainless Steel (SHXM4AY55N)",
        raw_content="""
<!DOCTYPE html>
<html>
<head><title>Bosch 100 Series SHXM4AY55N Built-In Dishwasher</title></head>
<body>
  <h1>Bosch 100 Series SHXM4AY55N 24 in Built-In Dishwasher</h1>
  <h2>Technical Specifications</h2>
  <table>
    <tr><th>Installation Type</th><td>Built-In</td></tr>
    <tr><th>Tub Material</th><td>Stainless Steel TallTub with Polypropylene Base</td></tr>
    <tr><th>Sound Level</th><td>48 dBA</td></tr>
    <tr><th>Number of Cycles</th><td>5</td></tr>
    <tr><th>Voltage Rating</th><td>120 V</td></tr>
    <tr><th>Amps</th><td>15 A</td></tr>
    <tr><th>Energy Star Qualified</th><td>Yes</td></tr>
    <tr><th>Place Settings</th><td>14</td></tr>
  </table>

  <h2>Dimensions</h2>
  <table>
    <tr><th>Width</th><td>23-9/16 in</td></tr>
    <tr><th>Height</th><td>33-7/8 in</td></tr>
    <tr><th>Depth</th><td>22-9/16 in</td></tr>
  </table>
</body>
</html>
"""
    ),

    # 4. GE Appliances GDT665SSNSS Official Specification Sheet
    SourceRegistrationRequest(
        url="https://www.geappliances.com/appliance/GE-Appliances-Stainless-Steel-Built-In-Dishwasher-GDT665SSNSS",
        mpn="GDT665SSNSS",
        brand="GE APPLIANCES™",
        manufacturer="GE Appliances, a Haier company",
        source_type=EvidenceType.MANUFACTURER_PAGE.value,
        title="GE Profile™ 24\" Built-In Dishwasher with Deep Clean Silverware Jets (GDT665SSNSS)",
        raw_content="""
<!DOCTYPE html>
<html>
<head><title>GE Appliances GDT665SSNSS Built-In Dishwasher</title></head>
<body>
  <h1>GE Appliances GDT665SSNSS 24 in Built-In Dishwasher</h1>
  <h2>Product Overview</h2>
  <table>
    <tr><th>Installation Type</th><td>Built-In</td></tr>
    <tr><th>Interior Tub Material</th><td>Stainless Steel</td></tr>
    <tr><th>Sound Level</th><td>48 dBA</td></tr>
    <tr><th>Number of Wash Cycles</th><td>5</td></tr>
    <tr><th>Place Settings</th><td>16</td></tr>
  </table>

  <h2>Electrical Ratings</h2>
  <table>
    <tr><th>Voltage</th><td>120 V</td></tr>
    <tr><th>Amperage</th><td>15 A</td></tr>
    <tr><th>Energy Star</th><td>Yes</td></tr>
  </table>

  <h2>Dimensions</h2>
  <table>
    <tr><th>Overall Width</th><td>23-3/4 in</td></tr>
    <tr><th>Overall Height</th><td>34 in</td></tr>
    <tr><th>Overall Depth</th><td>24 in</td></tr>
  </table>
</body>
</html>
"""
    ),

    # 9. Diablo DCB518ASTS06G Official Product Page (1/2 in. x 18 in. Sanding Belt Assorted 6-Pack)
    SourceRegistrationRequest(
        url="https://www.diablotools.com/products/DCB518ASTS06G",
        mpn="DCB518ASTS06G",
        brand="DIABLO®",
        manufacturer="Freud America, Inc.",
        source_type=EvidenceType.MANUFACTURER_PAGE.value,
        title="Diablo 1/2 in. x 18 in. Sanding Belt Assorted 6-Pack (DCB518ASTS06G)",
        raw_content="""
<!DOCTYPE html>
<html>
<head><title>Diablo DCB518ASTS06G 1/2 in x 18 in Sanding Belt 6pc Specification</title></head>
<body>
  <h1>Diablo DCB518ASTS06G 1/2 in. x 18 in. Sanding Belt Assorted 6-Pack</h1>
  <h2>Technical Specifications</h2>
  <table>
    <tr><th>Abrasive Type</th><td>Sanding Belt</td></tr>
    <tr><th>Material</th><td>Zirconia Alumina</td></tr>
    <tr><th>Belt Width</th><td>1/2 in</td></tr>
    <tr><th>Belt Length</th><td>18 in</td></tr>
    <tr><th>Grit</th><td>Assorted</td></tr>
    <tr><th>Backing Material</th><td>Cloth</td></tr>
    <tr><th>Package Quantity</th><td>6</td></tr>
  </table>
  <h2>Application Details</h2>
  <p>Premium Zirconia Alumina grain blend for aggressive material removal and extended sanding belt life on metal, wood, and plastic.</p>
</body>
</html>
"""
    )
]


def seed_demo_evidence():
    """Seed the 4 representative demo products into the source registry."""
    mgr = EvidenceRegistryManager()
    results = []
    for req in DEMO_EVIDENCE_PAYLOADS:
        res = mgr.register_source(req)
        results.append(res)
    return results


if __name__ == "__main__":
    results = seed_demo_evidence()
    for r in results:
        print(f"[{r.source_status}] {r.source_id}: {r.message} (Chunks: {r.chunks_count})")
