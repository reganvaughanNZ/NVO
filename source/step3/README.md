# Step 3: preview clarification

Create an Object script named NVOStartPreview using NVOStartPreview.txt and compile it.

In ALTBackgroundMenu replace:

    let sMSGDesc := GetFormDescription rBackMsg

with:

    let sMSGDesc := Call NVOStartPreview iButton

Compile ALTBackgroundMenu and save NVO.esm. The helper keeps donor descriptions and adds selected warnings and common start information. It does not change starting equipment, quest state, or faction relationships.

GECK compilation and gameplay testing are handled by the user. This source has not been compiled or tested by the assistant.
