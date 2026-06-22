You will be provided with an OCR-parsed text of a materials science paper.

=== INPUT TEXT START ===
{paper_text}
=== INPUT TEXT END ===

Execute the extraction workflow below, strictly complying with all system prompt rules and the unified JSON data Schema:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 1: Global Metadata & Role Discrimination (Target vs Reference)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Extract paper Title and DOI to the root `Paper_Metadata` object.
- 【IMPORTANT】: To maximize data richness, extract both the paper's core developed and tested material (Target)
  and benchmark/reference data from other literature used for comparison (Reference).
  You MUST isolate them using `"Role": "Reference"` in `Composition_Info`; the paper's own data = `"Target"`.
  Any data with "[x]" citation markers or from introductions/reviews is definitely Reference.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 2: Item Decomposition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Identify ALL distinct material variants. Any change in (composition, elements) or (process conditions, orientation)
  MUST trigger creation of a new independent object in the `"items": []` array.
- 【Gradient Materials】: If the material has a composition/microstructure gradient along a direction,
  set `Gradient_Material: true` and express composition as ranges.
  Only split by layer into multiple Items when the literature explicitly provides independent data per layer,
  linked via `Gradient_Group_ID`.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 3: Composition Extraction (`Composition_Info`)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Extract nominal composition (`Nominal_Composition`) and measured composition (`Measured_Composition`), normalize strictly to 100%.
- 【Composition Format】Default format is `"Element_Symbol": numeric_value`, e.g., `"Ni": 53.0`, `"Fe": 18.5`.
  For special notations (ranges, upper limits, impurity notes, etc.), describe them in the top-level `Note` field.
  Example: `"Note": "C content ≤0.08%, S content ≤0.015%, P content ≤0.015%, all as upper limit notations; Nb content is 5.0-5.5% range"`
- If total sums to <100% with no residual element specified, add `"other"` to balance to 100.0; if `"other"` is negative, do NOT add the key.
- For commercial grades (e.g., Inconel 718, 316L SS) lacking specific composition values,
  keep `Alloy_Name_Raw` and set `Elements_Normalized` to `null`.
- If measured composition specifies an analytical method (e.g., "EDS", "ICP", "chemical analysis"), fill the `Measurement_Method` field; if not provided, set to `null`.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 4: Process Extraction (`Process_Info`)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Double-track process description text (`original` and `simplified`).
  **【IMPORTANT】** The `original` field must extract the **full and detailed** process description from the source text without any simplification; the `simplified` field retains key information and removes redundancy, but do NOT over-simplify.
- If the literature mentions specific equipment models or manufacturers, extract to `Equipment` field (e.g., "EOS M290", "vacuum induction melting furnace"); if not mentioned, set to `null`.
- Extract quantified parameters to `Key_Params` using canonical names (e.g., `Laser_Power_W`, `Solution_Temperature_K`).
- 【Heat Treatment Range Values】: If temperature or time is a range (e.g., "1000-1100°C", "2-4h"),
  preserve the original range string, do NOT average — e.g., `"Solution_Temperature_K": "1273-1373"`.
- Multi-stage heat treatment must use stage suffixes like `_Stage1_K`; NEVER average different stage temperatures.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 5: Microstructure Extraction (`Microstructure_Info`)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Double-track microstructure text (`original` and `simplified`).
  **【IMPORTANT】** The `original` field must extract the **full and detailed** microstructure description from the source text without any simplification; the `simplified` field retains key information and removes redundancy, but do NOT over-simplify.
- 【Main_Phase Identification】: In Ni/Co/Fe-based alloys, Main_Phase should be Gamma (γ) matrix or FCC/BCC;
  precipitates (Laves, MC/M₂C/M₆C Carbide, Gamma Prime (γ'), etc.) go in the `Precipitates[]` array.
  **ABSOLUTELY PROHIBITED** from identifying Laves or Carbides as Main_Phase!
- 【Relative Density】: Fill strictly as provided in the literature; if not mentioned → `null`.
  **NEVER** infer as 100% (this is hallucination).
- Extract Tier 1/2 quantitative parameters (porosity, grain size, precipitate size/fraction, etc.) to root fields;
  advanced physical parameters (dislocation density, etc.) go to `Advanced_Quantitative_Features` with unit suffixes.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 6: Properties Extraction (`Properties_Info` — Maximum Error Zone)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Collect ALL mechanical/physical test results under the same Item (different temperatures, strain rates, etc.)
  into `Properties_Info`, strictly ordered Tier 1 → Tier 2 → Tier 3.
- 【Three-Way Elongation Distinction】:
  * `Elongation_Total`: Total elongation, commonly labeled as "Elongation" or "A"
  * `Elongation_Uniform`: Uniform elongation before necking, may be labeled as "A<sub>g</sub>"
  * `Elongation_At_Fracture`: Elongation at fracture
  * If the literature only provides one "Elongation" without distinction, default to `Elongation_Total`
    and note it.
- 【Tensile Test Conditions】: MUST extract strain rate and tensile speed:
  * `Strain_Rate_s1` (strain rate, unit s⁻¹)
  * `Tensile_Speed_mm_min` (tensile speed, crosshead speed, unit mm/min)
- 【Hardness Test Conditions】: MUST extract load and dwell time:
  * `Hardness_Load` (indentation load, with unit, e.g., "200gf", "0.98N")
  * `Hardness_Dwell_Time_s` (dwell time, in seconds, typical 15s)
- 【Temperature Isolation Wall】: `Test_Temperature_K` is ONLY for the test environment temperature.
  NEVER fill fabrication/heat treatment temperatures here. Room temperature = 298.15 K.
- 【Tensile-Compressive Mutual Exclusion】: In compressive test scenarios, ALL property names
  MUST carry `_Compressive` suffix. Never mix tensile and compressive indicators.
- 【Format Rules】:
  * Range values (e.g., 200-230): `Value_Numeric` = range mean, `Value_Range` = original range string
  * Tolerance (e.g., 215±5): `Value_Numeric` = main value, `Value_StdDev` = tolerance
  * Data source: text tables → `"text"`, charts/images → `"image"`
- 【Test Specimen】: If the literature provides specimen dimensions or applicable standards (e.g., ASTM E8, GB/T 228),
  annotate in `Test_Specimen` field.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 7: Final Reflective Checkgate (Mandatory Self-Audit)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Before outputting JSON, immediately perform these internal checks:
- 【Hallucination Prevention】: Were any fields that should be `null` (especially relative density) filled with guessed data (like 100%)?
  Any data not provided in the literature MUST remain `null`!
- 【Reference Contamination】: Did all data with "[x]" markers or from introductions/reviews get marked `Role: "Reference"`?
- 【Missing Extremes】: Were high/low temperature or small variant data hidden deep in tables or mentioned in one sentence all captured?
- 【Unit Confusion】: Are MPa values mistakenly in % fields? Are tensile and compressive properties mixed up?
- 【Elongation Tripartition】: Have total, uniform, and fracture elongation been correctly distinguished?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Step 8: Output
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Verify root-level `Paper_Metadata` and all four primary object structures are complete.
- Output ONLY a single valid JSON string — no conversational text, no Markdown code fences (```).
  Start output from `{"Paper_Metadata": ` and end cleanly at `]}`.
