# Step 4: quick/custom character setup

Apply these three edits to ALTStartQscript in GECK. Do not replace the whole script with an older workspace copy.

Add this variable before the first Begin block:

```text
Int iQuickStart
```

Replace the existing ElseIf iStage == 1 branch, stopping before ElseIf iStage == 2:

```text
    ElseIf iStage == 1
        iStage = -2
        let rLambda := (Begin function {int iSetupChoice}
            if iSetupChoice == 0
                let iQuickStart := 1
                let iStage := 3
            else
                let iQuickStart := 0
                let iStage := 1.5
            endif
        End)
        let svString := "^Character Setup^Quick keeps your current name and appearance and starts at level 1."
        let svString += " Custom lets you change your name, appearance and starting level."
        let svString += " Both let you choose SPECIAL, skills, traits and survival options."
        let svString += "|Quick Setup|Custom Setup"
        MessageBoxExAlt rLambda "%z" svString
    ElseIf iStage == 1.5
        GetPlayerName
        iStage = 2
```

Replace the stage 8 section, stopping immediately before ElseIf iStage == 10:

```text
    ElseIf iStage == 8
        if iQuickStart == 1
            set ALTLevelQ.iLevel to 1
            set iStage to 10
            return
        endif

        svString = GetStringSetting "sHowMany"
        SetStringSetting "sHowMany" "Choose Starting Level"
        let rLambda := (Begin function {int iChosenLevel}
            set ALTLevelQ.iLevel to iChosenLevel
            set ALTStartQ.iStage to 10
        End)
        iStage = 9
        ShowQuantityMenu rLambda 20 1
        SetStringSetting "sHowMany" $svString
```

The user reported successful compilation after these callback fixes. The current GECK source has not been re-exported, so this document records the supplied edits, not a verified export. Gameplay testing is performed by the user. The assistant has not compiled or tested the edit.
