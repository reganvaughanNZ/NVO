# Step 6: correct the Random Start configuration lookup

In ALTBackRandomUDF, change only the GetINIFloat key from Random:bNoRandomDLC to All:bNoRandomDLC. The supplied full source records that one functional change and normalizes whitespace.

Evidence: release/NVO/Data/config/ALTStartConfig.ini places bNoRandomDLC under [All], whereas the extracted donor ALTBackRandomUDF reads [Random]. With the supplied configuration, enabling the documented setting therefore does not affect the donor lookup.

The fix respects the existing setting: 0 still permits DLC starts and 1 excludes background IDs 55 through 58. It does not alter the INI, when the random background is rolled, or the equipment and world changes performed by the selected background.

The user reported successful compilation and saving NVO.esm. No ESM or installed game file was edited by this source preparation, and no compilation or gameplay testing was performed by the assistant.
