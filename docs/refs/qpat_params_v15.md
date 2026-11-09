# Iridium/Quantum .qpat v15 – vollständige Parameter-Referenz

Zum Nachschlagen: jeder v15-Parameter mit **allen beobachteten `value → display`-Paaren**
(Enum-Shifts zwischen Versionen werden so sichtbar, z. B. `OscType Off`: v8=4, v14=4, v15=6).

## Quellen (alle `version=15`)

- `dumps/export-003/03100-Far Out.qpat` — Factory-Preset 3100 "Far Out" (export-003); 3810 Params, name='Far Out'
- `dumps/00000-.qpat` — Init/Empty (frischer Geraete-Export); 3811 Params, name=''
- `dumps/00202-SH Power.qpat` — SH Power Testreihe, F2=Off; 3811 Params, name='SH Power'

**v15-Parameter gesamt: 3430** | davon nur in v15 (nicht in v8-Exporten): 2180 | nur in v8: 1

## Parametertabelle (alphabetisch)

| Parameter | beobachtete Werte (`value → display`) |
|---|---|
| `4` | `0`; `0` → Humble Bell |
| `AfterTouchAmount` | `0`; `0.5` |
| `AfterTouchAttack` | `0.1` |
| `AfterTouchDoPoly` | `1` → Poly AT |
| `AfterTouchKey` | `0` |
| `AfterTouchRelease` | `0.01` |
| `AfterTouchValue` | `0` |
| `AmpEnvAttack` | `0`; `0.01` |
| `AmpEnvAttackCurve` | `1` → RC |
| `AmpEnvDecay` | `0.409449`; `0.7` |
| `AmpEnvDecayCurve` | `0` → Exp |
| `AmpEnvDelay` | `0` |
| `AmpEnvLoopMode` | `0` → - |
| `AmpEnvRelease` | `0.1`; `0.110236`; `0.794721` |
| `AmpEnvReleaseCurve` | `0` → Exp |
| `AmpEnvSingleTrig` | `0` → Off |
| `AmpEnvSustain` | `1` |
| `AmpVeloAmount` | `0.5`; `0.503937` |
| `ArpAlgo` | `0` → Up |
| `ArpGate` | `0.5`; `0.8` |
| `ArpOct` | `0` → 1 oct; `2` → 3 oct |
| `ArpOn` | `0` → Off |
| `ArpPattern` | `0` → 1 |
| `ArpReset` | `0` → Off |
| `ArpSeqToMidiOut` | `1` → On |
| `ArpSortOrder` | `2` → Key Lo>Hi |
| `ArpStepLength` | `10` → 1/16 |
| `ArpSwing` | `0.5` |
| `ArpVeloMode` | `0` → Each Note |
| `ButtonPress` | `0` |
| `CCGotMapped` | `0` → 0 |
| `CV1Range` | `1` |
| `CV2Range` | `1` |
| `CV3Range` | `1` |
| `CV4Range` | `1` |
| `CVClockDivider` | `7` → 1/24 |
| `CalibDisplayHorizotal` | `0` → 0 |
| `CalibDisplayVertical` | `0` → 0 |
| `CalibTouchVertical` | `0` |
| `ChangeProgram` | `0` |
| `ChangeTimbre` | `0` |
| `ChordLatch` | `0` → Off |
| `ChordMode` | `0` → Off |
| `ChorusDelay` | `0.06` |
| `ChorusDepth` | `0.4` |
| `ChorusDryWet` | `0`; `0.75` |
| `ChorusFeedback` | `0.5` |
| `ChorusHighCut` | `0` |
| `ChorusLowCut` | `0` |
| `ChorusPhase` | `0.75` |
| `ChorusShape` | `1` → Sine |
| `ChorusSpeed` | `0.2` |
| `ChorusStages` | `1` → 4 |
| `CodecRecLevel` | `0.843137` |
| `CompressorAttack` | `0`; `0.2` |
| `CompressorAutoGain` | `1` → On |
| `CompressorInputGain` | `0.27`; `0.5` |
| `CompressorLookAhead` | `0.5` |
| `CompressorOutputGain` | `0.5`; `0.76` |
| `CompressorRatio` | `0.35`; `0.42` |
| `CompressorRelease` | `0.2`; `0.27` |
| `CompressorThreshold` | `0.5`; `0.81` |
| `CoreSelectedVariation` | `0` → 1 |
| `DelayDecouple` | `0` |
| `DelayDelayL` | `0.3` |
| `DelayDelayR` | `0.35` |
| `DelayDryWet` | `0`; `0.5` |
| `DelayFeed` | `0.75` |
| `DelayHiCut` | `0` |
| `DelayLeftSync` | `6` → 1/8 |
| `DelayLink` | `1` → On |
| `DelayLowCut` | `0` |
| `DelayRightSync` | `6` → 1/8 |
| `DelaySync` | `0` → Off; `1` → On |
| `DelayXPan` | `0.7` |
| `Development1` | `0` |
| `Development2` | `0` |
| `Development3` | `0` |
| `Development4` | `0` |
| `Development5` | `0` |
| `Development6` | `0` |
| `DigiFormerAmount` | `0` |
| `DigiFormerColor` | `0`; `0.619746` |
| `DigiFormerKeytrack` | `0.5` |
| `DigiFormerLevel` | `0.5` |
| `DigiFormerPan` | `0.5` |
| `DigiFormerTilt` | `0.5` |
| `DigiFormerType` | `0` → Bypass |
| `DriveAmount` | `0.3` |
| `DriveDryWet` | `0.5` |
| `DriveGain` | `0.5` |
| `DriveType` | `0` → PNP |
| `EnvGroupSelect` | `0` → Filt 1 |
| `EnvelopeVariation` | `0.35` |
| `EqFreqShift` | `0.5` |
| `EqHighFreq` | `0.9` |
| `EqHighGain` | `0.5` |
| `EqHighOnOff` | `1` → On |
| `EqLowFreq` | `0.1` |
| `EqLowGain` | `0.5` |
| `EqLowOnOff` | `1` → On |
| `EqMasterGain` | `1` |
| `EqMid2Freq` | `0.6` |
| `EqMid2Gain` | `0.5` |
| `EqMid2OnOff` | `1` → On |
| `EqMid2Q` | `0.7` |
| `EqMidFreq` | `0.3` |
| `EqMidGain` | `0.5` |
| `EqMidOnOff` | `1` → On |
| `EqMidQ` | `0.7` |
| `EqOverallGain` | `0.5` |
| `FX1Bypass` | `0` → Active |
| `FX1Type` | `0` → Off; `3` → Chorus |
| `FX2Bypass` | `0` → Active |
| `FX2Type` | `0` → Off; `5` → Delay |
| `FX3Bypass` | `0` → Active |
| `FX3Type` | `0` → Off |
| `FX4Bypass` | `0` → Active |
| `FX4Type` | `0` → Off; `6` → Reverb |
| `FX5Bypass` | `0` → Active |
| `FX5Type` | `0` → Off |
| `FXLanel1Level` | `1` |
| `FXLanel1Pan` | `0.5` |
| `FXLanel2Level` | `1` |
| `FXLanel2Pan` | `0.5` |
| `FXLanel3Level` | `1` |
| `FXLanel3Pan` | `0.5` |
| `FXOffControl` | `0` |
| `FXOffDryWet` | `0`; `0.458456` |
| `FXRouting` | `0` → 5 serial |
| `FXTotalDryWet` | `1` |
| `Filter12Type` | `0` → 12dB LP; `3` → 24dB LP |
| `Filter1AttackCurve` | `1` → RC |
| `Filter1CutOff` | `0.25`; `1` |
| `Filter1DecayCurve` | `0` → Exp |
| `Filter1EnvAmount` | `0.5`; `0.637795` |
| `Filter1EnvAttack` | `0`; `0.01` |
| `Filter1EnvDecay` | `0.393701`; `0.7` |
| `Filter1EnvDelay` | `0` |
| `Filter1EnvRelease` | `0.393701`; `0.5` |
| `Filter1EnvSingleTrig` | `0` → Off |
| `Filter1EnvSustain` | `0`; `0.1` |
| `Filter1Keytrack` | `0.5` |
| `Filter1LoopMode` | `0` → - |
| `Filter1Model` | `0` → Svf |
| `Filter1ReleaseCurve` | `0` → Exp |
| `Filter1Reso` | `0`; `0.401575` |
| `Filter1VeloAmount` | `0.5`; `0.503937` |
| `Filter2AttackCurve` | `1` → RC |
| `Filter2CutOff` | `0`; `1` |
| `Filter2DecayCurve` | `0` → Exp |
| `Filter2EnvAmount` | `0.5`; `1` |
| `Filter2EnvAttack` | `0`; `0.01` |
| `Filter2EnvDecay` | `0.393701`; `0.7` |
| `Filter2EnvDelay` | `0` |
| `Filter2EnvRelease` | `0.393701`; `0.5` |
| `Filter2EnvSingleTrig` | `0` → Off |
| `Filter2EnvSustain` | `0`; `0.1` |
| `Filter2Keytrack` | `0`; `0.5` |
| `Filter2Level` | `1` |
| `Filter2LoopMode` | `0` → - |
| `Filter2Model` | `0` → Svf |
| `Filter2Pan` | `0.5` |
| `Filter2ReleaseCurve` | `0` → Exp |
| `Filter2Reso` | `0` |
| `Filter2State` | `0` → Active; `2` → Off |
| `Filter2Type` | `0` → 12dB LP |
| `Filter2VeloAmount` | `0.5`; `0.503937` |
| `FilterDomain` | `1` → Digital |
| `FilterFormerRouting` | `1` → Filter > Former |
| `FilterLevel` | `1` |
| `FilterLink` | `0` → Single; `6` → Independent |
| `FilterPan` | `0.5` |
| `FilterState` | `0` → Active |
| `FilterStereoMode` | `0` → Neutral; `2` → Strong |
| `FinalColor` | `1` → On |
| `FlangerCenter` | `0` |
| `FlangerDepth` | `0.65` |
| `FlangerDryWet` | `0.5` |
| `FlangerFeedback` | `0.6` |
| `FlangerPhase` | `0.5` |
| `FlangerShape` | `0` → Triangle |
| `FlangerSpeed` | `0.3` |
| `Flavour` | `0` |
| `FlavourEnv` | `0.35` |
| `FlavourFilter` | `0.25` |
| `FlavourOsc1` | `0.5` |
| `FlavourOsc2` | `0.5` |
| `FlavourOsc3` | `0.5` |
| `FlavourPan` | `0.2` |
| `FlavourPitch` | `0.45` |
| `FlavourTiming` | `0.5` |
| `FlavourVol` | `0.15` |
| `FreeEnv1Amount` | `0.5` |
| `FreeEnv1Attack` | `0`; `0.01` |
| `FreeEnv1AttackCurve` | `1` → RC |
| `FreeEnv1Decay` | `0.503937`; `0.7`; `0.76` |
| `FreeEnv1DecayCurve` | `0` → Exp |
| `FreeEnv1Delay` | `0` |
| `FreeEnv1LoopMode` | `0` → - |
| `FreeEnv1Release` | `0.5`; `0.503937` |
| `FreeEnv1ReleaseCurve` | `0` → Exp |
| `FreeEnv1SingleTrig` | `0` → Off |
| `FreeEnv1Sustain` | `0`; `0.503937` |
| `FreeEnv1VeloAmount` | `0.5` |
| `FreeEnv2Amount` | `0.5` |
| `FreeEnv2Attack` | `0`; `0.01` |
| `FreeEnv2AttackCurve` | `1` → RC |
| `FreeEnv2Decay` | `0.503937`; `0.7` |
| `FreeEnv2DecayCurve` | `0` → Exp |
| `FreeEnv2Delay` | `0` |
| `FreeEnv2LoopMode` | `0` → - |
| `FreeEnv2Release` | `0.5`; `0.503937` |
| `FreeEnv2ReleaseCurve` | `0` → Exp |
| `FreeEnv2SingleTrig` | `0` → Off |
| `FreeEnv2Sustain` | `0`; `0.1`; `0.503937` |
| `FreeEnv2VeloAmount` | `0.5` |
| `FreeEnv3Amount` | `0.5` |
| `FreeEnv3Attack` | `0.01` |
| `FreeEnv3AttackCurve` | `1` → RC |
| `FreeEnv3Decay` | `0.7` |
| `FreeEnv3DecayCurve` | `0` → Exp |
| `FreeEnv3Delay` | `0` |
| `FreeEnv3LoopMode` | `0` → - |
| `FreeEnv3Release` | `0.5` |
| `FreeEnv3ReleaseCurve` | `0` → Exp |
| `FreeEnv3SingleTrig` | `0` → Off |
| `FreeEnv3Sustain` | `0`; `0.1` |
| `FreeEnv3VeloAmount` | `0.5` |
| `GlideOnOff` | `0` → Off |
| `GlideRate` | `0.15`; `0.15748` |
| `GlideType` | `0` → Onset |
| `GlobalOutRoutingOverride` | `0` → Patch |
| `GlobalSendsAux` | `0` → Off |
| `GlobalSendsMain` | `1` → On |
| `IRPadChange` | `1` |
| `IRPadChordsMap` | `0`; `1` |
| `IRPadChordsMap2` | `0` |
| `IRPadChordsMode` | `0` → Free |
| `IRPadLatch` | `0` → Latch Off |
| `IRPadLatchMap` | `0`; `5` |
| `IRPadLatchMode` | `0` → Multi |
| `IRPadMode` | `0` → Notes |
| `IRPadNotesMap` | `0` |
| `IRPadOct` | `5` → Oct 3 |
| `IRPadScale` | `5` → Major |
| `IRPadScaleRoot` | `0` → C |
| `IRPadSelChordType` | `0` → Major |
| `IRPadSelChordVoicing` | `0` → Root |
| `IRPadSelected` | `0` → Row 1 Col 1 |
| `IRPadSelectedNote1` | `0` → C-2 |
| `IRPadSelectedNoteActive1` | `0` → (Note 1) |
| `IRPadTriggerAlgo` | `0` → LR Up |
| `IRPadVelo` | `0.8` |
| `InputRouting` | `1` → Main Output |
| `InputVolume` | `0` |
| `KeyboardOctOffset` | `2` → 0; `3` → 0 |
| `KeymapNote` | `0` → C-2 |
| `KeytrackAmount` | `0`; `0.5` |
| `KomplexAmount` | `0.5` |
| `KomplexDelay` | `0` |
| `KomplexEntropy` | `0` |
| `KomplexEnvelope` | `0` |
| `KomplexGlobal` | `0` → Poly |
| `KomplexNumStepsA` | `6` → 8 |
| `KomplexNumStepsB` | `6` → 8 |
| `KomplexPhase` | `0` |
| `KomplexShape` | `0` |
| `KomplexSlew` | `0.4` |
| `KomplexSpeed` | `0.5` |
| `KomplexStep10ACurveType` | `0` → Lin |
| `KomplexStep10ACurveVal` | `0.5` |
| `KomplexStep10ALevel` | `0.5` |
| `KomplexStep10BCurveType` | `0` → Lin |
| `KomplexStep10BCurveVal` | `0.5` |
| `KomplexStep10BLevel` | `0.5` |
| `KomplexStep11ACurveType` | `0` → Lin |
| `KomplexStep11ACurveVal` | `0.5` |
| `KomplexStep11ALevel` | `0.5` |
| `KomplexStep11BCurveType` | `0` → Lin |
| `KomplexStep11BCurveVal` | `0.5` |
| `KomplexStep11BLevel` | `0.5` |
| `KomplexStep12ACurveType` | `0` → Lin |
| `KomplexStep12ACurveVal` | `0.5` |
| `KomplexStep12ALevel` | `0.5` |
| `KomplexStep12BCurveType` | `0` → Lin |
| `KomplexStep12BCurveVal` | `0.5` |
| `KomplexStep12BLevel` | `0.5` |
| `KomplexStep13ACurveType` | `0` → Lin |
| `KomplexStep13ACurveVal` | `0.5` |
| `KomplexStep13ALevel` | `0.5` |
| `KomplexStep13BCurveType` | `0` → Lin |
| `KomplexStep13BCurveVal` | `0.5` |
| `KomplexStep13BLevel` | `0.5` |
| `KomplexStep14ACurveType` | `0` → Lin |
| `KomplexStep14ACurveVal` | `0.5` |
| `KomplexStep14ALevel` | `0.5` |
| `KomplexStep14BCurveType` | `0` → Lin |
| `KomplexStep14BCurveVal` | `0.5` |
| `KomplexStep14BLevel` | `0.5` |
| `KomplexStep15ACurveType` | `0` → Lin |
| `KomplexStep15ACurveVal` | `0.5` |
| `KomplexStep15ALevel` | `0.5` |
| `KomplexStep15BCurveType` | `0` → Lin |
| `KomplexStep15BCurveVal` | `0.5` |
| `KomplexStep15BLevel` | `0.5` |
| `KomplexStep16ACurveType` | `0` → Lin |
| `KomplexStep16ACurveVal` | `0.5` |
| `KomplexStep16ALevel` | `0.5` |
| `KomplexStep16BCurveType` | `0` → Lin |
| `KomplexStep16BCurveVal` | `0.5` |
| `KomplexStep16BLevel` | `0.5` |
| `KomplexStep17ACurveType` | `0` → Lin |
| `KomplexStep17ACurveVal` | `0.5` |
| `KomplexStep17ALevel` | `0.5` |
| `KomplexStep17BCurveType` | `0` → Lin |
| `KomplexStep17BCurveVal` | `0.5` |
| `KomplexStep17BLevel` | `0.5` |
| `KomplexStep18ACurveType` | `0` → Lin |
| `KomplexStep18ACurveVal` | `0.5` |
| `KomplexStep18ALevel` | `0.5` |
| `KomplexStep18BCurveType` | `0` → Lin |
| `KomplexStep18BCurveVal` | `0.5` |
| `KomplexStep18BLevel` | `0.5` |
| `KomplexStep19ACurveType` | `0` → Lin |
| `KomplexStep19ACurveVal` | `0.5` |
| `KomplexStep19ALevel` | `0.5` |
| `KomplexStep19BCurveType` | `0` → Lin |
| `KomplexStep19BCurveVal` | `0.5` |
| `KomplexStep19BLevel` | `0.5` |
| `KomplexStep1ACurveType` | `0` → Lin |
| `KomplexStep1ACurveVal` | `0.5` |
| `KomplexStep1ALevel` | `0` |
| `KomplexStep1BCurveType` | `0` → Lin |
| `KomplexStep1BCurveVal` | `0.5` |
| `KomplexStep1BLevel` | `0` |
| `KomplexStep20ACurveType` | `0` → Lin |
| `KomplexStep20ACurveVal` | `0.5` |
| `KomplexStep20ALevel` | `0.5` |
| `KomplexStep20BCurveType` | `0` → Lin |
| `KomplexStep20BCurveVal` | `0.5` |
| `KomplexStep20BLevel` | `0.5` |
| `KomplexStep21ACurveType` | `0` → Lin |
| `KomplexStep21ACurveVal` | `0.5` |
| `KomplexStep21ALevel` | `0.5` |
| `KomplexStep21BCurveType` | `0` → Lin |
| `KomplexStep21BCurveVal` | `0.5` |
| `KomplexStep21BLevel` | `0.5` |
| `KomplexStep22ACurveType` | `0` → Lin |
| `KomplexStep22ACurveVal` | `0.5` |
| `KomplexStep22ALevel` | `0.5` |
| `KomplexStep22BCurveType` | `0` → Lin |
| `KomplexStep22BCurveVal` | `0.5` |
| `KomplexStep22BLevel` | `0.5` |
| `KomplexStep23ACurveType` | `0` → Lin |
| `KomplexStep23ACurveVal` | `0.5` |
| `KomplexStep23ALevel` | `0.5` |
| `KomplexStep23BCurveType` | `0` → Lin |
| `KomplexStep23BCurveVal` | `0.5` |
| `KomplexStep23BLevel` | `0.5` |
| `KomplexStep24ACurveType` | `0` → Lin |
| `KomplexStep24ACurveVal` | `0.5` |
| `KomplexStep24ALevel` | `0.5` |
| `KomplexStep24BCurveType` | `0` → Lin |
| `KomplexStep24BCurveVal` | `0.5` |
| `KomplexStep24BLevel` | `0.5` |
| `KomplexStep25ACurveType` | `0` → Lin |
| `KomplexStep25ACurveVal` | `0.5` |
| `KomplexStep25ALevel` | `0.5` |
| `KomplexStep25BCurveType` | `0` → Lin |
| `KomplexStep25BCurveVal` | `0.5` |
| `KomplexStep25BLevel` | `0.5` |
| `KomplexStep26ACurveType` | `0` → Lin |
| `KomplexStep26ACurveVal` | `0.5` |
| `KomplexStep26ALevel` | `0.5` |
| `KomplexStep26BCurveType` | `0` → Lin |
| `KomplexStep26BCurveVal` | `0.5` |
| `KomplexStep26BLevel` | `0.5` |
| `KomplexStep27ACurveType` | `0` → Lin |
| `KomplexStep27ACurveVal` | `0.5` |
| `KomplexStep27ALevel` | `0.5` |
| `KomplexStep27BCurveType` | `0` → Lin |
| `KomplexStep27BCurveVal` | `0.5` |
| `KomplexStep27BLevel` | `0.5` |
| `KomplexStep28ACurveType` | `0` → Lin |
| `KomplexStep28ACurveVal` | `0.5` |
| `KomplexStep28ALevel` | `0.5` |
| `KomplexStep28BCurveType` | `0` → Lin |
| `KomplexStep28BCurveVal` | `0.5` |
| `KomplexStep28BLevel` | `0.5` |
| `KomplexStep29ACurveType` | `0` → Lin |
| `KomplexStep29ACurveVal` | `0.5` |
| `KomplexStep29ALevel` | `0.5` |
| `KomplexStep29BCurveType` | `0` → Lin |
| `KomplexStep29BCurveVal` | `0.5` |
| `KomplexStep29BLevel` | `0.5` |
| `KomplexStep2ACurveType` | `0` → Lin |
| `KomplexStep2ACurveVal` | `0.5` |
| `KomplexStep2ALevel` | `0.142857` |
| `KomplexStep2BCurveType` | `0` → Lin |
| `KomplexStep2BCurveVal` | `0.5` |
| `KomplexStep2BLevel` | `0.142857` |
| `KomplexStep30ACurveType` | `0` → Lin |
| `KomplexStep30ACurveVal` | `0.5` |
| `KomplexStep30ALevel` | `0.5` |
| `KomplexStep30BCurveType` | `0` → Lin |
| `KomplexStep30BCurveVal` | `0.5` |
| `KomplexStep30BLevel` | `0.5` |
| `KomplexStep31ACurveType` | `0` → Lin |
| `KomplexStep31ACurveVal` | `0.5` |
| `KomplexStep31ALevel` | `0.5` |
| `KomplexStep31BCurveType` | `0` → Lin |
| `KomplexStep31BCurveVal` | `0.5` |
| `KomplexStep31BLevel` | `0.5` |
| `KomplexStep32ACurveType` | `0` → Lin |
| `KomplexStep32ACurveVal` | `0.5` |
| `KomplexStep32ALevel` | `0.5` |
| `KomplexStep32BCurveType` | `0` → Lin |
| `KomplexStep32BCurveVal` | `0.5` |
| `KomplexStep32BLevel` | `0.5` |
| `KomplexStep3ACurveType` | `0` → Lin |
| `KomplexStep3ACurveVal` | `0.5` |
| `KomplexStep3ALevel` | `0.285714` |
| `KomplexStep3BCurveType` | `0` → Lin |
| `KomplexStep3BCurveVal` | `0.5` |
| `KomplexStep3BLevel` | `0.285714` |
| `KomplexStep4ACurveType` | `0` → Lin |
| `KomplexStep4ACurveVal` | `0.5` |
| `KomplexStep4ALevel` | `0.428571` |
| `KomplexStep4BCurveType` | `0` → Lin |
| `KomplexStep4BCurveVal` | `0.5` |
| `KomplexStep4BLevel` | `0.428571` |
| `KomplexStep5ACurveType` | `0` → Lin |
| `KomplexStep5ACurveVal` | `0.5` |
| `KomplexStep5ALevel` | `0.571429` |
| `KomplexStep5BCurveType` | `0` → Lin |
| `KomplexStep5BCurveVal` | `0.5` |
| `KomplexStep5BLevel` | `0.571429` |
| `KomplexStep6ACurveType` | `0` → Lin |
| `KomplexStep6ACurveVal` | `0.5` |
| `KomplexStep6ALevel` | `0.714286` |
| `KomplexStep6BCurveType` | `0` → Lin |
| `KomplexStep6BCurveVal` | `0.5` |
| `KomplexStep6BLevel` | `0.714286` |
| `KomplexStep7ACurveType` | `0` → Lin |
| `KomplexStep7ACurveVal` | `0.5` |
| `KomplexStep7ALevel` | `0.857143` |
| `KomplexStep7BCurveType` | `0` → Lin |
| `KomplexStep7BCurveVal` | `0.5` |
| `KomplexStep7BLevel` | `0.857143` |
| `KomplexStep8ACurveType` | `0` → Lin |
| `KomplexStep8ACurveVal` | `0.5` |
| `KomplexStep8ALevel` | `1` |
| `KomplexStep8BCurveType` | `0` → Lin |
| `KomplexStep8BCurveVal` | `0.5` |
| `KomplexStep8BLevel` | `1` |
| `KomplexStep9ACurveType` | `0` → Lin |
| `KomplexStep9ACurveVal` | `0.5` |
| `KomplexStep9ALevel` | `0.5` |
| `KomplexStep9BCurveType` | `0` → Lin |
| `KomplexStep9BCurveVal` | `0.5` |
| `KomplexStep9BLevel` | `0.5` |
| `KomplexStepASelection` | `0` → 1 |
| `KomplexStepBSelection` | `0` → 1 |
| `KomplexSync` | `0` → Off |
| `KomplexSyncRatio` | `22` → 1/4 trip; `23` → 1/8 |
| `KomplexWarp` | `0.5` |
| `LFOSelect` | `0` → LFO 1 |
| `LastNotePlayed` | `72`; `6187`; `6192` |
| `LastNoteReleased` | `60`; `6151`; `6155` |
| `LastPressedKey` | `0` |
| `Latch` | `0` → Off |
| `LayerActive` | `1` → Active |
| `LayerGain` | `0`; `0.59` |
| `LayerMaxNote` | `127` → G8 |
| `LayerMinNote` | `0` → C-2 |
| `LayerPan` | `0.5` |
| `LayerSplitMaxKey` | `23` → B2 |
| `LayerSplitMinKey` | `0` → C1 |
| `LayerVoices` | `3` → 4; `4` → 5 |
| `LayerVolume` | `1` |
| `Lfo1Amount` | `0.5` |
| `Lfo1Attack` | `0` |
| `Lfo1Decay` | `1` |
| `Lfo1Delay` | `0` |
| `Lfo1Global` | `0` → Poly |
| `Lfo1Phase` | `0` |
| `Lfo1Polarity` | `0` → Bipolar |
| `Lfo1Shape` | `0` → Sine |
| `Lfo1Slew` | `0.4` |
| `Lfo1Speed` | `0.5` |
| `Lfo1Sync` | `0` → Off |
| `Lfo1SyncRatio` | `22` → 1/4 trip; `23` → 1/8 |
| `Lfo1Warp` | `0.5` |
| `Lfo2Amount` | `0.5` |
| `Lfo2Attack` | `0` |
| `Lfo2Decay` | `1` |
| `Lfo2Delay` | `0` |
| `Lfo2Global` | `0` → Poly |
| `Lfo2Phase` | `0` |
| `Lfo2Polarity` | `0` → Bipolar |
| `Lfo2Shape` | `0` → Sine |
| `Lfo2Slew` | `0.4` |
| `Lfo2Speed` | `0.5` |
| `Lfo2Sync` | `0` → Off |
| `Lfo2SyncRatio` | `22` → 1/4 trip; `23` → 1/8 |
| `Lfo2Warp` | `0.5` |
| `Lfo3Amount` | `0.5` |
| `Lfo3Attack` | `0` |
| `Lfo3Decay` | `1` |
| `Lfo3Delay` | `0` |
| `Lfo3Global` | `0` → Poly |
| `Lfo3Phase` | `0` |
| `Lfo3Polarity` | `0` → Bipolar |
| `Lfo3Shape` | `0` → Sine |
| `Lfo3Slew` | `0.4` |
| `Lfo3Speed` | `0.5` |
| `Lfo3Sync` | `0` → Off |
| `Lfo3SyncRatio` | `22` → 1/4 trip; `23` → 1/8 |
| `Lfo3Warp` | `0.5` |
| `Lfo4Amount` | `0.5` |
| `Lfo4Attack` | `0` |
| `Lfo4Decay` | `1` |
| `Lfo4Delay` | `0` |
| `Lfo4Global` | `0` → Poly |
| `Lfo4Phase` | `0` |
| `Lfo4Polarity` | `0` → Bipolar |
| `Lfo4Shape` | `0` → Sine |
| `Lfo4Slew` | `0.4` |
| `Lfo4Speed` | `0.5` |
| `Lfo4Sync` | `0` → Off |
| `Lfo4SyncRatio` | `22` → 1/4 trip; `23` → 1/8 |
| `Lfo4Warp` | `0.5` |
| `Lfo5Amount` | `0.5` |
| `Lfo5Attack` | `0` |
| `Lfo5Decay` | `1` |
| `Lfo5Delay` | `0` |
| `Lfo5Global` | `0` → Poly |
| `Lfo5Phase` | `0` |
| `Lfo5Polarity` | `0` → Bipolar |
| `Lfo5Shape` | `0` → Sine |
| `Lfo5Slew` | `0.4` |
| `Lfo5Speed` | `0.5` |
| `Lfo5Sync` | `0` → Off |
| `Lfo5SyncRatio` | `22` → 1/4 trip; `23` → 1/8 |
| `Lfo5Warp` | `0.5` |
| `Lfo6Amount` | `0.5` |
| `Lfo6Attack` | `0` |
| `Lfo6Decay` | `1` |
| `Lfo6Delay` | `0` |
| `Lfo6Global` | `0` → Poly |
| `Lfo6Phase` | `0` |
| `Lfo6Polarity` | `0` → Bipolar |
| `Lfo6Shape` | `0` → Sine |
| `Lfo6Slew` | `0.4` |
| `Lfo6Speed` | `0.5` |
| `Lfo6Sync` | `0` → Off |
| `Lfo6SyncRatio` | `22` → 1/4 trip; `23` → 1/8 |
| `Lfo6Warp` | `0.5` |
| `LoadAttributeFilter` | `0` |
| `LoadAuthorFilter` | `0` |
| `LoadBankFilter` | `0`; `6` |
| `LoadFeatureFilter` | `0` → All |
| `LocalControllerMode` | `0` → All |
| `Macro1` | `0` → Off |
| `Macro2` | `0` → Off |
| `Macro3` | `0` → Off |
| `Macro4` | `0` → Off |
| `Macro5` | `0` → Off |
| `Macro6` | `0` → Off |
| `MainCompression` | `0` |
| `MainVolume` | `0.815249`; `0.999022` |
| `MatrixAmount1` | `0.5`; `0.57874`; `0.68` |
| `MatrixAmount10` | `0.5` |
| `MatrixAmount11` | `0.5` |
| `MatrixAmount12` | `0.5` |
| `MatrixAmount13` | `0.5` |
| `MatrixAmount14` | `0.5` |
| `MatrixAmount15` | `0.5` |
| `MatrixAmount16` | `0.5` |
| `MatrixAmount17` | `0.5` |
| `MatrixAmount18` | `0.5` |
| `MatrixAmount19` | `0.5` |
| `MatrixAmount2` | `0.417323`; `0.5` |
| `MatrixAmount20` | `0.5` |
| `MatrixAmount21` | `0.5` |
| `MatrixAmount22` | `0.5` |
| `MatrixAmount23` | `0.5` |
| `MatrixAmount24` | `0.5` |
| `MatrixAmount25` | `0.5` |
| `MatrixAmount26` | `0.5` |
| `MatrixAmount27` | `0.5` |
| `MatrixAmount28` | `0.5` |
| `MatrixAmount29` | `0.5` |
| `MatrixAmount3` | `0.314961`; `0.5` |
| `MatrixAmount30` | `0.5` |
| `MatrixAmount31` | `0.5` |
| `MatrixAmount32` | `0.5` |
| `MatrixAmount33` | `0.5` |
| `MatrixAmount34` | `0.5` |
| `MatrixAmount35` | `0.5` |
| `MatrixAmount36` | `0.5` |
| `MatrixAmount37` | `0.5` |
| `MatrixAmount38` | `0.5` |
| `MatrixAmount39` | `0.5` |
| `MatrixAmount4` | `0.5`; `0.649606` |
| `MatrixAmount40` | `0.24`; `0.5` |
| `MatrixAmount5` | `0.5`; `0.700787` |
| `MatrixAmount6` | `0.5`; `0.622047` |
| `MatrixAmount7` | `0.5`; `0.685039` |
| `MatrixAmount8` | `0.5`; `0.51` |
| `MatrixAmount9` | `0.49`; `0.5` |
| `MatrixControl1` | `0` → Off |
| `MatrixControl10` | `0` → Off |
| `MatrixControl11` | `0` → Off |
| `MatrixControl12` | `0` → Off |
| `MatrixControl13` | `0` → Off |
| `MatrixControl14` | `0` → Off |
| `MatrixControl15` | `0` → Off |
| `MatrixControl16` | `0` → Off |
| `MatrixControl17` | `0` → Off |
| `MatrixControl18` | `0` → Off |
| `MatrixControl19` | `0` → Off |
| `MatrixControl2` | `0` → Off; `14` → Wheel |
| `MatrixControl20` | `0` → Off |
| `MatrixControl21` | `0` → Off |
| `MatrixControl22` | `0` → Off |
| `MatrixControl23` | `0` → Off |
| `MatrixControl24` | `0` → Off |
| `MatrixControl25` | `0` → Off |
| `MatrixControl26` | `0` → Off |
| `MatrixControl27` | `0` → Off |
| `MatrixControl28` | `0` → Off |
| `MatrixControl29` | `0` → Off |
| `MatrixControl3` | `0` → Off; `33` → Velocity |
| `MatrixControl30` | `0` → Off |
| `MatrixControl31` | `0` → Off |
| `MatrixControl32` | `0` → Off |
| `MatrixControl33` | `0` → Off |
| `MatrixControl34` | `0` → Off |
| `MatrixControl35` | `0` → Off |
| `MatrixControl36` | `0` → Off |
| `MatrixControl37` | `0` → Off |
| `MatrixControl38` | `0` → Off |
| `MatrixControl39` | `0` → Off |
| `MatrixControl4` | `0` → Off |
| `MatrixControl40` | `0` → Off |
| `MatrixControl5` | `0` → Off |
| `MatrixControl6` | `0` → Off |
| `MatrixControl7` | `0` → Off |
| `MatrixControl8` | `0` → Off |
| `MatrixControl9` | `0` → Off |
| `MatrixControlAmount1` | `0.5` |
| `MatrixControlAmount10` | `0.5` |
| `MatrixControlAmount11` | `0.5` |
| `MatrixControlAmount12` | `0.5` |
| `MatrixControlAmount13` | `0.5` |
| `MatrixControlAmount14` | `0.5` |
| `MatrixControlAmount15` | `0.5` |
| `MatrixControlAmount16` | `0.5` |
| `MatrixControlAmount17` | `0.5` |
| `MatrixControlAmount18` | `0.5` |
| `MatrixControlAmount19` | `0.5` |
| `MatrixControlAmount2` | `0.5`; `0.55` |
| `MatrixControlAmount20` | `0.5` |
| `MatrixControlAmount21` | `0.5` |
| `MatrixControlAmount22` | `0.5` |
| `MatrixControlAmount23` | `0.5` |
| `MatrixControlAmount24` | `0.5` |
| `MatrixControlAmount25` | `0.5` |
| `MatrixControlAmount26` | `0.5` |
| `MatrixControlAmount27` | `0.5` |
| `MatrixControlAmount28` | `0.5` |
| `MatrixControlAmount29` | `0.5` |
| `MatrixControlAmount3` | `0.43`; `0.5` |
| `MatrixControlAmount30` | `0.5` |
| `MatrixControlAmount31` | `0.5` |
| `MatrixControlAmount32` | `0.5` |
| `MatrixControlAmount33` | `0.5` |
| `MatrixControlAmount34` | `0.5` |
| `MatrixControlAmount35` | `0.5` |
| `MatrixControlAmount36` | `0.5` |
| `MatrixControlAmount37` | `0.5` |
| `MatrixControlAmount38` | `0.5` |
| `MatrixControlAmount39` | `0.5` |
| `MatrixControlAmount4` | `0.5` |
| `MatrixControlAmount40` | `0.5` |
| `MatrixControlAmount5` | `0.5` |
| `MatrixControlAmount6` | `0.5` |
| `MatrixControlAmount7` | `0.5` |
| `MatrixControlAmount8` | `0.5` |
| `MatrixControlAmount9` | `0.5` |
| `MatrixDst1` | `0` → Off; `1` → Pitch; `39` → SD1 Position |
| `MatrixDst10` | `0` → Off |
| `MatrixDst11` | `0` → Off |
| `MatrixDst12` | `0` → Off |
| `MatrixDst13` | `0` → Off |
| `MatrixDst14` | `0` → Off |
| `MatrixDst15` | `0` → Off |
| `MatrixDst16` | `0` → Off |
| `MatrixDst17` | `0` → Off |
| `MatrixDst18` | `0` → Off |
| `MatrixDst19` | `0` → Off |
| `MatrixDst2` | `0` → Off; `1` → Pitch; `3` → Osc2 Pitch |
| `MatrixDst20` | `0` → Off |
| `MatrixDst21` | `0` → Off |
| `MatrixDst22` | `0` → Off |
| `MatrixDst23` | `0` → Off |
| `MatrixDst24` | `0` → Off |
| `MatrixDst25` | `0` → Off |
| `MatrixDst26` | `0` → Off |
| `MatrixDst27` | `0` → Off |
| `MatrixDst28` | `0` → Off |
| `MatrixDst29` | `0` → Off |
| `MatrixDst3` | `0` → Off; `124` → Filt1Env Sustain |
| `MatrixDst30` | `0` → Off |
| `MatrixDst31` | `0` → Off |
| `MatrixDst32` | `0` → Off |
| `MatrixDst33` | `0` → Off |
| `MatrixDst34` | `0` → Off |
| `MatrixDst35` | `0` → Off |
| `MatrixDst36` | `0` → Off |
| `MatrixDst37` | `0` → Off |
| `MatrixDst38` | `0` → Off |
| `MatrixDst39` | `0` → Off |
| `MatrixDst4` | `0` → Off; `123` → Filt1Env Decay |
| `MatrixDst40` | `0` → Off; `152` → Volume |
| `MatrixDst5` | `0` → Off; `109` → Filter1 Cutoff |
| `MatrixDst6` | `0` → Off; `110` → Filter1 Reso |
| `MatrixDst7` | `0` → Off; `109` → Filter1 Cutoff |
| `MatrixDst8` | `0` → Off; `2` → Osc1 Pitch |
| `MatrixDst9` | `0` → Off; `3` → Osc2 Pitch |
| `MatrixOnOff1` | `1` → Active |
| `MatrixOnOff10` | `1` → Active |
| `MatrixOnOff11` | `1` → Active |
| `MatrixOnOff12` | `1` → Active |
| `MatrixOnOff13` | `1` → Active |
| `MatrixOnOff14` | `1` → Active |
| `MatrixOnOff15` | `1` → Active |
| `MatrixOnOff16` | `1` → Active |
| `MatrixOnOff17` | `1` → Active |
| `MatrixOnOff18` | `1` → Active |
| `MatrixOnOff19` | `1` → Active |
| `MatrixOnOff2` | `1` → Active |
| `MatrixOnOff20` | `1` → Active |
| `MatrixOnOff21` | `1` → Active |
| `MatrixOnOff22` | `1` → Active |
| `MatrixOnOff23` | `1` → Active |
| `MatrixOnOff24` | `1` → Active |
| `MatrixOnOff25` | `1` → Active |
| `MatrixOnOff26` | `1` → Active |
| `MatrixOnOff27` | `1` → Active |
| `MatrixOnOff28` | `1` → Active |
| `MatrixOnOff29` | `1` → Active |
| `MatrixOnOff3` | `1` → Active |
| `MatrixOnOff30` | `1` → Active |
| `MatrixOnOff31` | `1` → Active |
| `MatrixOnOff32` | `1` → Active |
| `MatrixOnOff33` | `1` → Active |
| `MatrixOnOff34` | `1` → Active |
| `MatrixOnOff35` | `1` → Active |
| `MatrixOnOff36` | `1` → Active |
| `MatrixOnOff37` | `1` → Active |
| `MatrixOnOff38` | `1` → Active |
| `MatrixOnOff39` | `1` → Active |
| `MatrixOnOff4` | `1` → Active |
| `MatrixOnOff40` | `1` → Active |
| `MatrixOnOff5` | `1` → Active |
| `MatrixOnOff6` | `1` → Active |
| `MatrixOnOff7` | `1` → Active |
| `MatrixOnOff8` | `1` → Active |
| `MatrixOnOff9` | `1` → Active |
| `MatrixSlotSelection` | `0` → 1; `1` → 2; `5` → 6 |
| `MatrixSrc1` | `0` → Off; `14` → Wheel; `17` → After Touch |
| `MatrixSrc10` | `0` → Off |
| `MatrixSrc11` | `0` → Off |
| `MatrixSrc12` | `0` → Off |
| `MatrixSrc13` | `0` → Off |
| `MatrixSrc14` | `0` → Off |
| `MatrixSrc15` | `0` → Off |
| `MatrixSrc16` | `0` → Off |
| `MatrixSrc17` | `0` → Off |
| `MatrixSrc18` | `0` → Off |
| `MatrixSrc19` | `0` → Off |
| `MatrixSrc2` | `0` → Off; `7` → LFO 1; `17` → After Touch |
| `MatrixSrc20` | `0` → Off |
| `MatrixSrc21` | `0` → Off |
| `MatrixSrc22` | `0` → Off |
| `MatrixSrc23` | `0` → Off |
| `MatrixSrc24` | `0` → Off |
| `MatrixSrc25` | `0` → Off |
| `MatrixSrc26` | `0` → Off |
| `MatrixSrc27` | `0` → Off |
| `MatrixSrc28` | `0` → Off |
| `MatrixSrc29` | `0` → Off |
| `MatrixSrc3` | `0` → Off; `14` → Wheel |
| `MatrixSrc30` | `0` → Off |
| `MatrixSrc31` | `0` → Off |
| `MatrixSrc32` | `0` → Off |
| `MatrixSrc33` | `0` → Off |
| `MatrixSrc34` | `0` → Off |
| `MatrixSrc35` | `0` → Off |
| `MatrixSrc36` | `0` → Off |
| `MatrixSrc37` | `0` → Off |
| `MatrixSrc38` | `0` → Off |
| `MatrixSrc39` | `0` → Off |
| `MatrixSrc4` | `0` → Off; `14` → Wheel |
| `MatrixSrc40` | `0` → Off; `40` → Constant |
| `MatrixSrc5` | `0` → Off; `33` → Velocity |
| `MatrixSrc6` | `0` → Off; `33` → Velocity |
| `MatrixSrc7` | `0` → Off; `14` → Wheel |
| `MatrixSrc8` | `0` → Off; `17` → After Touch |
| `MatrixSrc9` | `0` → Off; `17` → After Touch |
| `MultiAllocMode` | `0` → Layered |
| `MultiArpMode` | `0` → Individual Layer |
| `MutatorAllAmount` | `0` |
| `MutatorEffectsAmount` | `0` |
| `MutatorEnvelopesAmount` | `0` |
| `MutatorFilterAmount` | `0` |
| `MutatorModulationAmount` | `0` |
| `MutatorOscAmount` | `0` |
| `MutatorPitchAmount` | `0` |
| `Osc1CoarsePitch` | `24` → +0 semi |
| `Osc1Destination` | `0` → Main; `2` → DF 0 Fil 100 |
| `Osc1FinePitch` | `0.5`; `0.503937` |
| `Osc1ForceRetrigger` | `0` → No |
| `Osc1Keytrack` | `0.75` |
| `Osc1MaxNote` | `127` → G8 |
| `Osc1MinNote` | `0` → C-2 |
| `Osc1Pan` | `0`; `0.5` |
| `Osc1ParticleAttack` | `0.25` |
| `Osc1ParticleCount` | `3` → 4; `7` → 8 |
| `Osc1ParticleDecay` | `0.25` |
| `Osc1ParticleGain` | `0.1` |
| `Osc1ParticleGate` | `1` |
| `Osc1ParticleJitter` | `0` |
| `Osc1ParticleLength` | `0.125`; `0.5` |
| `Osc1ParticlePitchJitter` | `0` |
| `Osc1ParticlePitchMapVal1` | `0` → 0 |
| `Osc1ParticlePitchMapVal2` | `0` → 0 |
| `Osc1ParticlePitchMapVal3` | `0` → 0 |
| `Osc1ParticlePitchMapVal4` | `0` → 0 |
| `Osc1ParticlePitchMapVal5` | `0` → 0 |
| `Osc1ParticlePitchMapVal6` | `0` → 0 |
| `Osc1ParticlePitchMode` | `1` → Cluster |
| `Osc1ParticlePitchSpread` | `0.1` |
| `Osc1ParticlePos` | `0.1` |
| `Osc1ParticlePosSpread` | `0.3` |
| `Osc1ParticleSampleMode` | `2` → Normal |
| `Osc1ParticleSelectionRule` | `0` → Round Robin |
| `Osc1ParticleStereoWidth` | `0.5` |
| `Osc1ParticleTravel` | `0.5` |
| `Osc1ParticleTravelMode` | `0` → Continuous |
| `Osc1PitchBendRange` | `36` → +12 |
| `Osc1ResonatorColor` | `0.5`; `0.504399` |
| `Osc1ResonatorColorMode` | `0` → Peak Mod; `2` → Saw-Square |
| `Osc1ResonatorColorSkew` | `0.25` |
| `Osc1ResonatorDensity` | `0.42131`; `0.68` |
| `Osc1ResonatorEnvAttack` | `0` |
| `Osc1ResonatorEnvDecay` | `0.1` |
| `Osc1ResonatorF0Boost` | `0.15` |
| `Osc1ResonatorHiCut` | `0.1` |
| `Osc1ResonatorModes` | `1` |
| `Osc1ResonatorNoisy` | `0` |
| `Osc1ResonatorRepeatAccel` | `0.5` |
| `Osc1ResonatorRepeats` | `0` → 1 |
| `Osc1ResonatorSpread` | `0.5`; `0.615233` |
| `Osc1ResonatorSpreadMode` | `0` → Stretch; `1` → Stiffness |
| `Osc1ResonatorStereoWidth` | `0.25`; `0.5` |
| `Osc1ResonatorTimbre` | `0.2`; `0.32` |
| `Osc1Type` | `0` → Wavetable; `1` → Waveform; `5` → Seeds |
| `Osc1Vol` | `1` |
| `Osc1WaveformDesity` | `0` |
| `Osc1WaveformPW` | `0.5`; `1` |
| `Osc1WaveformResetPhase` | `0` → Running |
| `Osc1WaveformSemitone1` | `12` → +0 |
| `Osc1WaveformSemitone2` | `12` → +0 |
| `Osc1WaveformSemitone3` | `12` → +0 |
| `Osc1WaveformSemitone4` | `12` → +0 |
| `Osc1WaveformShape` | `0` → Sawtooth |
| `Osc1WaveformSpread` | `0.25` |
| `Osc1WaveformStereoWidth` | `0.5` |
| `Osc1WaveformSync` | `0` |
| `Osc1WavetableBrilliance` | `0` |
| `Osc1WavetableDrive` | `0` |
| `Osc1WavetableFXType` | `2` → Truncate; `3` → Drive |
| `Osc1WavetableKeytrack` | `1` |
| `Osc1WavetableLimited` | `1` → Limit |
| `Osc1WavetableMode` | `0` → Normal |
| `Osc1WavetableNoisy` | `0` |
| `Osc1WavetablePhase` | `0` |
| `Osc1WavetablePosition` | `0` |
| `Osc1WavetableSpectrum` | `0.5` |
| `Osc1WavetableStepped` | `0` → Smooth |
| `Osc1WavetableTable` | `0` → Resonant  |
| `Osc1WavetableTableChanged` | `0` |
| `Osc1WavetableTravel` | `0.5` |
| `Osc1WavetableTravelMode` | `3` → One Shot; `4` → Ping Pong |
| `Osc1WavetableTravelSyncRatio` | `37` → 256 beats; `42` → 48 beats |
| `Osc2CoarsePitch` | `24` → +0 semi |
| `Osc2Destination` | `0` → Main; `2` → DF 0 Fil 100 |
| `Osc2FinePitch` | `0.5`; `0.503937` |
| `Osc2ForceRetrigger` | `0` → No |
| `Osc2Keytrack` | `0.75` |
| `Osc2MaxNote` | `127` → G8 |
| `Osc2MinNote` | `0` → C-2 |
| `Osc2Pan` | `0`; `0.5` |
| `Osc2ParticleAttack` | `0.25` |
| `Osc2ParticleCount` | `3` → 4; `7` → 8 |
| `Osc2ParticleDecay` | `0.25` |
| `Osc2ParticleGain` | `0.1` |
| `Osc2ParticleGate` | `1` |
| `Osc2ParticleJitter` | `0` |
| `Osc2ParticleLength` | `0.125`; `0.5` |
| `Osc2ParticlePitchJitter` | `0` |
| `Osc2ParticlePitchMapVal1` | `0` → 0 |
| `Osc2ParticlePitchMapVal2` | `0` → 0 |
| `Osc2ParticlePitchMapVal3` | `0` → 0 |
| `Osc2ParticlePitchMapVal4` | `0` → 0 |
| `Osc2ParticlePitchMapVal5` | `0` → 0 |
| `Osc2ParticlePitchMapVal6` | `0` → 0 |
| `Osc2ParticlePitchMode` | `1` → Cluster |
| `Osc2ParticlePitchSpread` | `0.1` |
| `Osc2ParticlePos` | `0.1` |
| `Osc2ParticlePosSpread` | `0.3` |
| `Osc2ParticleSampleMode` | `0` → Granular; `2` → Normal |
| `Osc2ParticleSelectionRule` | `0` → Round Robin |
| `Osc2ParticleStereoWidth` | `0.5` |
| `Osc2ParticleTravel` | `0.5` |
| `Osc2ParticleTravelMode` | `0` → Continuous |
| `Osc2PitchBendRange` | `36` → +12 |
| `Osc2ResonatorColor` | `0.5` |
| `Osc2ResonatorColorMode` | `0` → Peak Mod |
| `Osc2ResonatorColorSkew` | `0.25` |
| `Osc2ResonatorDensity` | `0.68` |
| `Osc2ResonatorEnvAttack` | `0` |
| `Osc2ResonatorEnvDecay` | `0.1` |
| `Osc2ResonatorF0Boost` | `0.15` |
| `Osc2ResonatorHiCut` | `0.1` |
| `Osc2ResonatorModes` | `1` |
| `Osc2ResonatorNoisy` | `0` |
| `Osc2ResonatorRepeatAccel` | `0.5` |
| `Osc2ResonatorRepeats` | `0` → 1 |
| `Osc2ResonatorSpread` | `0.5` |
| `Osc2ResonatorSpreadMode` | `0` → Stretch |
| `Osc2ResonatorStereoWidth` | `0.25`; `0.5` |
| `Osc2ResonatorTimbre` | `0.32` |
| `Osc2Type` | `1` → Waveform; `6` → Off |
| `Osc2Vol` | `0`; `0.700787` |
| `Osc2WaveformDesity` | `0`; `0.22` |
| `Osc2WaveformPW` | `0.5`; `1` |
| `Osc2WaveformResetPhase` | `0` → Running |
| `Osc2WaveformSemitone1` | `12` → +0 |
| `Osc2WaveformSemitone2` | `0` → -12; `12` → +0 |
| `Osc2WaveformSemitone3` | `12` → +0 |
| `Osc2WaveformSemitone4` | `12` → +0 |
| `Osc2WaveformShape` | `0` → Sawtooth; `3` → Square |
| `Osc2WaveformSpread` | `0.25`; `0.355816` |
| `Osc2WaveformStereoWidth` | `0.5` |
| `Osc2WaveformSync` | `0` |
| `Osc2WavetableBrilliance` | `0` |
| `Osc2WavetableDrive` | `0` |
| `Osc2WavetableFXType` | `2` → Truncate; `3` → Drive |
| `Osc2WavetableKeytrack` | `1` |
| `Osc2WavetableLimited` | `1` → Limit |
| `Osc2WavetableMode` | `0` → Normal |
| `Osc2WavetableNoisy` | `0` |
| `Osc2WavetablePhase` | `0` |
| `Osc2WavetablePosition` | `0`; `0.57087` |
| `Osc2WavetableSpectrum` | `0.5` |
| `Osc2WavetableStepped` | `0` → Smooth |
| `Osc2WavetableTable` | `0` → Resonant  |
| `Osc2WavetableTableChanged` | `0` |
| `Osc2WavetableTravel` | `0.5` |
| `Osc2WavetableTravelMode` | `3` → One Shot; `4` → Ping Pong |
| `Osc2WavetableTravelSyncRatio` | `37` → 256 beats; `42` → 48 beats |
| `Osc3CoarsePitch` | `24` → +0 semi |
| `Osc3Destination` | `0` → Main; `2` → DF 0 Fil 100 |
| `Osc3FinePitch` | `0.5`; `0.503937` |
| `Osc3ForceRetrigger` | `0` → No |
| `Osc3Keytrack` | `0.75` |
| `Osc3MaxNote` | `127` → G8 |
| `Osc3MinNote` | `0` → C-2 |
| `Osc3Pan` | `0`; `0.5` |
| `Osc3ParticleAttack` | `0.25` |
| `Osc3ParticleCount` | `3` → 4; `7` → 8 |
| `Osc3ParticleDecay` | `0.25` |
| `Osc3ParticleGain` | `0.1` |
| `Osc3ParticleGate` | `1` |
| `Osc3ParticleJitter` | `0` |
| `Osc3ParticleLength` | `0.125`; `0.5` |
| `Osc3ParticlePitchJitter` | `0` |
| `Osc3ParticlePitchMapVal1` | `0` → 0 |
| `Osc3ParticlePitchMapVal2` | `0` → 0 |
| `Osc3ParticlePitchMapVal3` | `0` → 0 |
| `Osc3ParticlePitchMapVal4` | `0` → 0 |
| `Osc3ParticlePitchMapVal5` | `0` → 0 |
| `Osc3ParticlePitchMapVal6` | `0` → 0 |
| `Osc3ParticlePitchMode` | `1` → Cluster |
| `Osc3ParticlePitchSpread` | `0.1` |
| `Osc3ParticlePos` | `0.1` |
| `Osc3ParticlePosSpread` | `0.3` |
| `Osc3ParticleSampleMode` | `2` → Normal |
| `Osc3ParticleSelectionRule` | `0` → Round Robin |
| `Osc3ParticleStereoWidth` | `0.5` |
| `Osc3ParticleTravel` | `0.5` |
| `Osc3ParticleTravelMode` | `0` → Continuous |
| `Osc3PitchBendRange` | `36` → +12 |
| `Osc3ResonatorColor` | `0.5` |
| `Osc3ResonatorColorMode` | `0` → Peak Mod |
| `Osc3ResonatorColorSkew` | `0.25` |
| `Osc3ResonatorDensity` | `0.68` |
| `Osc3ResonatorEnvAttack` | `0` |
| `Osc3ResonatorEnvDecay` | `0.1` |
| `Osc3ResonatorF0Boost` | `0.15` |
| `Osc3ResonatorHiCut` | `0.1` |
| `Osc3ResonatorModes` | `1` |
| `Osc3ResonatorNoisy` | `0` |
| `Osc3ResonatorRepeatAccel` | `0.5` |
| `Osc3ResonatorRepeats` | `0` → 1 |
| `Osc3ResonatorSpread` | `0.5` |
| `Osc3ResonatorSpreadMode` | `0` → Stretch |
| `Osc3ResonatorStereoWidth` | `0.25`; `0.5` |
| `Osc3ResonatorTimbre` | `0.32` |
| `Osc3Type` | `6` → Off |
| `Osc3Vol` | `0`; `1` |
| `Osc3WaveformDesity` | `0`; `1` |
| `Osc3WaveformPW` | `0.5`; `1` |
| `Osc3WaveformResetPhase` | `0` → Running |
| `Osc3WaveformSemitone1` | `0` → -12; `12` → +0 |
| `Osc3WaveformSemitone2` | `12` → +0 |
| `Osc3WaveformSemitone3` | `12` → +0 |
| `Osc3WaveformSemitone4` | `12` → +0 |
| `Osc3WaveformShape` | `0` → Sawtooth |
| `Osc3WaveformSpread` | `0.25`; `0.38` |
| `Osc3WaveformStereoWidth` | `0.5` |
| `Osc3WaveformSync` | `0` |
| `Osc3WavetableBrilliance` | `0` |
| `Osc3WavetableDrive` | `0` |
| `Osc3WavetableFXType` | `2` → Truncate; `3` → Drive |
| `Osc3WavetableKeytrack` | `1` |
| `Osc3WavetableLimited` | `1` → Limit |
| `Osc3WavetableMode` | `0` → Normal |
| `Osc3WavetableNoisy` | `0` |
| `Osc3WavetablePhase` | `0` |
| `Osc3WavetablePosition` | `0` |
| `Osc3WavetableSpectrum` | `0.5` |
| `Osc3WavetableStepped` | `0` → Smooth |
| `Osc3WavetableTable` | `0` → Resonant  |
| `Osc3WavetableTableChanged` | `0` |
| `Osc3WavetableTravel` | `0.5` |
| `Osc3WavetableTravelMode` | `3` → One Shot; `4` → Ping Pong |
| `Osc3WavetableTravelSyncRatio` | `37` → 256 beats; `42` → 48 beats |
| `Pad1CcNumX` | `0` → Off |
| `Pad1CcNumY` | `0` → Off |
| `Pad1Springback` | `0` → Off |
| `Pad1SpringbackY` | `0` → Off |
| `Pad1X` | `0.5` |
| `Pad1XPolarity` | `0` → Bipolar |
| `Pad1Y` | `0.5` |
| `Pad1YPolarity` | `0` → Bipolar |
| `ParamLockItem` | `0` → 1 |
| `ParamLockNote` | `0` → C-2 |
| `PedalAmount` | `0`; `0.5` |
| `PerNotePitchBend` | `2` → 24 |
| `PhaserDepth` | `0.3` |
| `PhaserDryWet` | `0.5` |
| `PhaserFeedback` | `0.6` |
| `PhaserFreq` | `0.5` |
| `PhaserModel` | `0` → Nave |
| `PhaserPhase` | `0.5` |
| `PhaserQ` | `0.7` |
| `PhaserShape` | `0` → Triangle |
| `PhaserSpeed` | `0.5` |
| `PhaserStages` | `2` → 8 |
| `PitchBendAmount` | `0`; `0.5` |
| `PitchVariation` | `0.17` |
| `PlaybackVolume` | `1` |
| `PlayerMode` | `0` → Off; `1` → Arp |
| `PolyArpFollow` | `1` → Follow 1 |
| `PolyArpLines` | `1` → 2 Voices |
| `PolyArpMode` | `0` → Mono |
| `PolyArpSkip` | `1` → Skip 1 |
| `PolyArpTranspose` | `12` → Transpose 12 |
| `PolyMonoMode` | `0` → Poly |
| `Pot1ModSrc` | `0` |
| `Pot1Param` | `0` |
| `Pot1Polarity` | `1` → Unipolar |
| `Pot2ModSrc` | `0` |
| `Pot2Param` | `0` |
| `Pot2Polarity` | `1` → Unipolar |
| `Pot3ModSrc` | `0` |
| `Pot3Param` | `0` |
| `Pot3Polarity` | `1` → Unipolar |
| `Pot4ModSrc` | `0` |
| `Pot4Param` | `0` |
| `Pot4Polarity` | `1` → Unipolar |
| `RecordingSource` | `0` → Main |
| `RecordingTrigger` | `0` → Manual |
| `ReverbColor` | `0.5` |
| `ReverbGain` | `0`; `0.3`; `0.43` |
| `ReverbModDepth` | `0.2` |
| `ReverbModRate` | `0.293365` |
| `ReverbPredelay` | `0.2`; `0.31` |
| `ReverbTime` | `0.5`; `0.69`; `0.88` |
| `ReverbXFade` | `0.5` |
| `RhythmSyncDownbeat` | `1` → On |
| `RingModOsc1ToOsc2` | `0` |
| `RingModOsc1ToOsc3` | `0` |
| `SeedsOsc1Count` | `1` → 2; `3` → 4 |
| `SeedsOsc1Detune` | `0.042033`; `0.05` |
| `SeedsOsc1EnvAmount` | `0.5`; `1` |
| `SeedsOsc1NumVectors` | `4` → 5 |
| `SeedsOsc1Position` | `0` |
| `SeedsOsc1SoloVector` | `0` → 1 |
| `SeedsOsc1Spread` | `0.7` |
| `SeedsOsc1Vec10DirtType` | `0` → White Noise |
| `SeedsOsc1Vec10FMFeedback` | `0.1` |
| `SeedsOsc1Vec10FMIndex` | `0.35` |
| `SeedsOsc1Vec10FMRatio` | `0.3125` |
| `SeedsOsc1Vec10FreqRatioPart1` | `0.0625` |
| `SeedsOsc1Vec10FreqRatioPart2` | `0.125` |
| `SeedsOsc1Vec10FreqRatioPart3` | `0.1875` |
| `SeedsOsc1Vec10FreqRatioPart4` | `0.25` |
| `SeedsOsc1Vec10RMRatio` | `0.34375` |
| `SeedsOsc1Vec10SeedType` | `4` → Dirt |
| `SeedsOsc1Vec10Transpose` | `0.5` |
| `SeedsOsc1Vec10VolPart1` | `1` |
| `SeedsOsc1Vec10VolPart2` | `0.875` |
| `SeedsOsc1Vec10VolPart3` | `0.75` |
| `SeedsOsc1Vec10VolPart4` | `0.625` |
| `SeedsOsc1Vec10Volume` | `0.7` |
| `SeedsOsc1Vec10Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc1Vec10WavetablePos` | `0.15` |
| `SeedsOsc1Vec10dirtReso` | `0` |
| `SeedsOsc1Vec10dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc1Vec11DirtType` | `0` → White Noise |
| `SeedsOsc1Vec11FMFeedback` | `0.1` |
| `SeedsOsc1Vec11FMIndex` | `0.35` |
| `SeedsOsc1Vec11FMRatio` | `0.3125` |
| `SeedsOsc1Vec11FreqRatioPart1` | `0.0625` |
| `SeedsOsc1Vec11FreqRatioPart2` | `0.125` |
| `SeedsOsc1Vec11FreqRatioPart3` | `0.1875` |
| `SeedsOsc1Vec11FreqRatioPart4` | `0.25` |
| `SeedsOsc1Vec11RMRatio` | `0.34375` |
| `SeedsOsc1Vec11SeedType` | `0` → Parts |
| `SeedsOsc1Vec11Transpose` | `0.5` |
| `SeedsOsc1Vec11VolPart1` | `1` |
| `SeedsOsc1Vec11VolPart2` | `0.875` |
| `SeedsOsc1Vec11VolPart3` | `0.75` |
| `SeedsOsc1Vec11VolPart4` | `0.625` |
| `SeedsOsc1Vec11Volume` | `0.7` |
| `SeedsOsc1Vec11Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc1Vec11WavetablePos` | `0.15` |
| `SeedsOsc1Vec11dirtReso` | `0` |
| `SeedsOsc1Vec11dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc1Vec12DirtType` | `0` → White Noise |
| `SeedsOsc1Vec12FMFeedback` | `0.1` |
| `SeedsOsc1Vec12FMIndex` | `0.35` |
| `SeedsOsc1Vec12FMRatio` | `0.3125` |
| `SeedsOsc1Vec12FreqRatioPart1` | `0.0625` |
| `SeedsOsc1Vec12FreqRatioPart2` | `0.125` |
| `SeedsOsc1Vec12FreqRatioPart3` | `0.1875` |
| `SeedsOsc1Vec12FreqRatioPart4` | `0.25` |
| `SeedsOsc1Vec12RMRatio` | `0.34375` |
| `SeedsOsc1Vec12SeedType` | `1` → Wave |
| `SeedsOsc1Vec12Transpose` | `0.5` |
| `SeedsOsc1Vec12VolPart1` | `1` |
| `SeedsOsc1Vec12VolPart2` | `0.875` |
| `SeedsOsc1Vec12VolPart3` | `0.75` |
| `SeedsOsc1Vec12VolPart4` | `0.625` |
| `SeedsOsc1Vec12Volume` | `0.7` |
| `SeedsOsc1Vec12Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc1Vec12WavetablePos` | `0.15` |
| `SeedsOsc1Vec12dirtReso` | `0` |
| `SeedsOsc1Vec12dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc1Vec1DirtType` | `0` → White Noise; `2` → Crackle |
| `SeedsOsc1Vec1FMFeedback` | `0.1` |
| `SeedsOsc1Vec1FMIndex` | `0.35` |
| `SeedsOsc1Vec1FMRatio` | `0.3125` |
| `SeedsOsc1Vec1FreqRatioPart1` | `0.0625` |
| `SeedsOsc1Vec1FreqRatioPart2` | `0.125` |
| `SeedsOsc1Vec1FreqRatioPart3` | `0.1875` |
| `SeedsOsc1Vec1FreqRatioPart4` | `0.25` |
| `SeedsOsc1Vec1RMRatio` | `0.34375` |
| `SeedsOsc1Vec1SeedType` | `0` → Parts; `4` → Dirt |
| `SeedsOsc1Vec1Transpose` | `0.5` |
| `SeedsOsc1Vec1VolPart1` | `1` |
| `SeedsOsc1Vec1VolPart2` | `0.875` |
| `SeedsOsc1Vec1VolPart3` | `0.75` |
| `SeedsOsc1Vec1VolPart4` | `0.625` |
| `SeedsOsc1Vec1Volume` | `0.7` |
| `SeedsOsc1Vec1Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc1Vec1WavetablePos` | `0.15` |
| `SeedsOsc1Vec1dirtReso` | `0`; `0.28` |
| `SeedsOsc1Vec1dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc1Vec2DirtType` | `0` → White Noise |
| `SeedsOsc1Vec2FMFeedback` | `0.1` |
| `SeedsOsc1Vec2FMIndex` | `0.35` |
| `SeedsOsc1Vec2FMRatio` | `0.3125` |
| `SeedsOsc1Vec2FreqRatioPart1` | `0.0625` |
| `SeedsOsc1Vec2FreqRatioPart2` | `0.125` |
| `SeedsOsc1Vec2FreqRatioPart3` | `0.1875` |
| `SeedsOsc1Vec2FreqRatioPart4` | `0.25` |
| `SeedsOsc1Vec2RMRatio` | `0.34375` |
| `SeedsOsc1Vec2SeedType` | `1` → Wave |
| `SeedsOsc1Vec2Transpose` | `0.25`; `0.5` |
| `SeedsOsc1Vec2VolPart1` | `1` |
| `SeedsOsc1Vec2VolPart2` | `0.875` |
| `SeedsOsc1Vec2VolPart3` | `0.75` |
| `SeedsOsc1Vec2VolPart4` | `0.625` |
| `SeedsOsc1Vec2Volume` | `0.463397`; `0.7` |
| `SeedsOsc1Vec2Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc1Vec2WavetablePos` | `0.15`; `0.43` |
| `SeedsOsc1Vec2dirtReso` | `0` |
| `SeedsOsc1Vec2dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc1Vec3DirtType` | `0` → White Noise |
| `SeedsOsc1Vec3FMFeedback` | `0.1` |
| `SeedsOsc1Vec3FMIndex` | `0.35` |
| `SeedsOsc1Vec3FMRatio` | `0.3125` |
| `SeedsOsc1Vec3FreqRatioPart1` | `0.0625` |
| `SeedsOsc1Vec3FreqRatioPart2` | `0.125` |
| `SeedsOsc1Vec3FreqRatioPart3` | `0.1875` |
| `SeedsOsc1Vec3FreqRatioPart4` | `0.25` |
| `SeedsOsc1Vec3RMRatio` | `0.34375` |
| `SeedsOsc1Vec3SeedType` | `2` → FM |
| `SeedsOsc1Vec3Transpose` | `0.5` |
| `SeedsOsc1Vec3VolPart1` | `1` |
| `SeedsOsc1Vec3VolPart2` | `0.875` |
| `SeedsOsc1Vec3VolPart3` | `0.75` |
| `SeedsOsc1Vec3VolPart4` | `0.625` |
| `SeedsOsc1Vec3Volume` | `0.250821`; `0.7` |
| `SeedsOsc1Vec3Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc1Vec3WavetablePos` | `0.15` |
| `SeedsOsc1Vec3dirtReso` | `0` |
| `SeedsOsc1Vec3dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc1Vec4DirtType` | `0` → White Noise |
| `SeedsOsc1Vec4FMFeedback` | `0.1` |
| `SeedsOsc1Vec4FMIndex` | `0.35` |
| `SeedsOsc1Vec4FMRatio` | `0.3125` |
| `SeedsOsc1Vec4FreqRatioPart1` | `0.0625` |
| `SeedsOsc1Vec4FreqRatioPart2` | `0.125` |
| `SeedsOsc1Vec4FreqRatioPart3` | `0.1875` |
| `SeedsOsc1Vec4FreqRatioPart4` | `0.25` |
| `SeedsOsc1Vec4RMRatio` | `0.34375` |
| `SeedsOsc1Vec4SeedType` | `3` → RM |
| `SeedsOsc1Vec4Transpose` | `0.5` |
| `SeedsOsc1Vec4VolPart1` | `1` |
| `SeedsOsc1Vec4VolPart2` | `0.875` |
| `SeedsOsc1Vec4VolPart3` | `0.75` |
| `SeedsOsc1Vec4VolPart4` | `0.625` |
| `SeedsOsc1Vec4Volume` | `0.22`; `0.7` |
| `SeedsOsc1Vec4Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc1Vec4WavetablePos` | `0.15` |
| `SeedsOsc1Vec4dirtReso` | `0` |
| `SeedsOsc1Vec4dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc1Vec5DirtType` | `0` → White Noise |
| `SeedsOsc1Vec5FMFeedback` | `0.1` |
| `SeedsOsc1Vec5FMIndex` | `0.35` |
| `SeedsOsc1Vec5FMRatio` | `0.3125` |
| `SeedsOsc1Vec5FreqRatioPart1` | `0.0625` |
| `SeedsOsc1Vec5FreqRatioPart2` | `0.125` |
| `SeedsOsc1Vec5FreqRatioPart3` | `0.1875` |
| `SeedsOsc1Vec5FreqRatioPart4` | `0.25` |
| `SeedsOsc1Vec5RMRatio` | `0.34375` |
| `SeedsOsc1Vec5SeedType` | `4` → Dirt |
| `SeedsOsc1Vec5Transpose` | `0.5` |
| `SeedsOsc1Vec5VolPart1` | `1` |
| `SeedsOsc1Vec5VolPart2` | `0.875` |
| `SeedsOsc1Vec5VolPart3` | `0.75` |
| `SeedsOsc1Vec5VolPart4` | `0.625` |
| `SeedsOsc1Vec5Volume` | `0.463397`; `0.7` |
| `SeedsOsc1Vec5Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc1Vec5WavetablePos` | `0.15` |
| `SeedsOsc1Vec5dirtReso` | `0`; `0.34` |
| `SeedsOsc1Vec5dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc1Vec6DirtType` | `0` → White Noise |
| `SeedsOsc1Vec6FMFeedback` | `0.1` |
| `SeedsOsc1Vec6FMIndex` | `0.35` |
| `SeedsOsc1Vec6FMRatio` | `0.3125` |
| `SeedsOsc1Vec6FreqRatioPart1` | `0.0625` |
| `SeedsOsc1Vec6FreqRatioPart2` | `0.125` |
| `SeedsOsc1Vec6FreqRatioPart3` | `0.1875` |
| `SeedsOsc1Vec6FreqRatioPart4` | `0.25` |
| `SeedsOsc1Vec6RMRatio` | `0.34375` |
| `SeedsOsc1Vec6SeedType` | `0` → Parts |
| `SeedsOsc1Vec6Transpose` | `0.5` |
| `SeedsOsc1Vec6VolPart1` | `1` |
| `SeedsOsc1Vec6VolPart2` | `0.875` |
| `SeedsOsc1Vec6VolPart3` | `0.75` |
| `SeedsOsc1Vec6VolPart4` | `0.625` |
| `SeedsOsc1Vec6Volume` | `0.7` |
| `SeedsOsc1Vec6Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc1Vec6WavetablePos` | `0.15` |
| `SeedsOsc1Vec6dirtReso` | `0` |
| `SeedsOsc1Vec6dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc1Vec7DirtType` | `0` → White Noise |
| `SeedsOsc1Vec7FMFeedback` | `0.1` |
| `SeedsOsc1Vec7FMIndex` | `0.35` |
| `SeedsOsc1Vec7FMRatio` | `0.3125` |
| `SeedsOsc1Vec7FreqRatioPart1` | `0.0625` |
| `SeedsOsc1Vec7FreqRatioPart2` | `0.125` |
| `SeedsOsc1Vec7FreqRatioPart3` | `0.1875` |
| `SeedsOsc1Vec7FreqRatioPart4` | `0.25` |
| `SeedsOsc1Vec7RMRatio` | `0.34375` |
| `SeedsOsc1Vec7SeedType` | `1` → Wave |
| `SeedsOsc1Vec7Transpose` | `0.5` |
| `SeedsOsc1Vec7VolPart1` | `1` |
| `SeedsOsc1Vec7VolPart2` | `0.875` |
| `SeedsOsc1Vec7VolPart3` | `0.75` |
| `SeedsOsc1Vec7VolPart4` | `0.625` |
| `SeedsOsc1Vec7Volume` | `0.7` |
| `SeedsOsc1Vec7Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc1Vec7WavetablePos` | `0.15` |
| `SeedsOsc1Vec7dirtReso` | `0` |
| `SeedsOsc1Vec7dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc1Vec8DirtType` | `0` → White Noise |
| `SeedsOsc1Vec8FMFeedback` | `0.1` |
| `SeedsOsc1Vec8FMIndex` | `0.35` |
| `SeedsOsc1Vec8FMRatio` | `0.3125` |
| `SeedsOsc1Vec8FreqRatioPart1` | `0.0625` |
| `SeedsOsc1Vec8FreqRatioPart2` | `0.125` |
| `SeedsOsc1Vec8FreqRatioPart3` | `0.1875` |
| `SeedsOsc1Vec8FreqRatioPart4` | `0.25` |
| `SeedsOsc1Vec8RMRatio` | `0.34375` |
| `SeedsOsc1Vec8SeedType` | `2` → FM |
| `SeedsOsc1Vec8Transpose` | `0.5` |
| `SeedsOsc1Vec8VolPart1` | `1` |
| `SeedsOsc1Vec8VolPart2` | `0.875` |
| `SeedsOsc1Vec8VolPart3` | `0.75` |
| `SeedsOsc1Vec8VolPart4` | `0.625` |
| `SeedsOsc1Vec8Volume` | `0.7` |
| `SeedsOsc1Vec8Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc1Vec8WavetablePos` | `0.15` |
| `SeedsOsc1Vec8dirtReso` | `0` |
| `SeedsOsc1Vec8dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc1Vec9DirtType` | `0` → White Noise |
| `SeedsOsc1Vec9FMFeedback` | `0.1` |
| `SeedsOsc1Vec9FMIndex` | `0.35` |
| `SeedsOsc1Vec9FMRatio` | `0.3125` |
| `SeedsOsc1Vec9FreqRatioPart1` | `0.0625` |
| `SeedsOsc1Vec9FreqRatioPart2` | `0.125` |
| `SeedsOsc1Vec9FreqRatioPart3` | `0.1875` |
| `SeedsOsc1Vec9FreqRatioPart4` | `0.25` |
| `SeedsOsc1Vec9RMRatio` | `0.34375` |
| `SeedsOsc1Vec9SeedType` | `3` → RM |
| `SeedsOsc1Vec9Transpose` | `0.5` |
| `SeedsOsc1Vec9VolPart1` | `1` |
| `SeedsOsc1Vec9VolPart2` | `0.875` |
| `SeedsOsc1Vec9VolPart3` | `0.75` |
| `SeedsOsc1Vec9VolPart4` | `0.625` |
| `SeedsOsc1Vec9Volume` | `0.7` |
| `SeedsOsc1Vec9Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc1Vec9WavetablePos` | `0.15` |
| `SeedsOsc1Vec9dirtReso` | `0` |
| `SeedsOsc1Vec9dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc2Count` | `1` → 2 |
| `SeedsOsc2Detune` | `0.05` |
| `SeedsOsc2EnvAmount` | `0.5` |
| `SeedsOsc2NumVectors` | `4` → 5 |
| `SeedsOsc2Position` | `0` |
| `SeedsOsc2SoloVector` | `0` → 1 |
| `SeedsOsc2Spread` | `0.7` |
| `SeedsOsc2Vec10DirtType` | `0` → White Noise |
| `SeedsOsc2Vec10FMFeedback` | `0.1` |
| `SeedsOsc2Vec10FMIndex` | `0.35` |
| `SeedsOsc2Vec10FMRatio` | `0.3125` |
| `SeedsOsc2Vec10FreqRatioPart1` | `0.0625` |
| `SeedsOsc2Vec10FreqRatioPart2` | `0.125` |
| `SeedsOsc2Vec10FreqRatioPart3` | `0.1875` |
| `SeedsOsc2Vec10FreqRatioPart4` | `0.25` |
| `SeedsOsc2Vec10RMRatio` | `0.34375` |
| `SeedsOsc2Vec10SeedType` | `4` → Dirt |
| `SeedsOsc2Vec10Transpose` | `0.5` |
| `SeedsOsc2Vec10VolPart1` | `1` |
| `SeedsOsc2Vec10VolPart2` | `0.875` |
| `SeedsOsc2Vec10VolPart3` | `0.75` |
| `SeedsOsc2Vec10VolPart4` | `0.625` |
| `SeedsOsc2Vec10Volume` | `0.7` |
| `SeedsOsc2Vec10Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc2Vec10WavetablePos` | `0.15` |
| `SeedsOsc2Vec10dirtReso` | `0` |
| `SeedsOsc2Vec10dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc2Vec11DirtType` | `0` → White Noise |
| `SeedsOsc2Vec11FMFeedback` | `0.1` |
| `SeedsOsc2Vec11FMIndex` | `0.35` |
| `SeedsOsc2Vec11FMRatio` | `0.3125` |
| `SeedsOsc2Vec11FreqRatioPart1` | `0.0625` |
| `SeedsOsc2Vec11FreqRatioPart2` | `0.125` |
| `SeedsOsc2Vec11FreqRatioPart3` | `0.1875` |
| `SeedsOsc2Vec11FreqRatioPart4` | `0.25` |
| `SeedsOsc2Vec11RMRatio` | `0.34375` |
| `SeedsOsc2Vec11SeedType` | `0` → Parts |
| `SeedsOsc2Vec11Transpose` | `0.5` |
| `SeedsOsc2Vec11VolPart1` | `1` |
| `SeedsOsc2Vec11VolPart2` | `0.875` |
| `SeedsOsc2Vec11VolPart3` | `0.75` |
| `SeedsOsc2Vec11VolPart4` | `0.625` |
| `SeedsOsc2Vec11Volume` | `0.7` |
| `SeedsOsc2Vec11Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc2Vec11WavetablePos` | `0.15` |
| `SeedsOsc2Vec11dirtReso` | `0` |
| `SeedsOsc2Vec11dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc2Vec12DirtType` | `0` → White Noise |
| `SeedsOsc2Vec12FMFeedback` | `0.1` |
| `SeedsOsc2Vec12FMIndex` | `0.35` |
| `SeedsOsc2Vec12FMRatio` | `0.3125` |
| `SeedsOsc2Vec12FreqRatioPart1` | `0.0625` |
| `SeedsOsc2Vec12FreqRatioPart2` | `0.125` |
| `SeedsOsc2Vec12FreqRatioPart3` | `0.1875` |
| `SeedsOsc2Vec12FreqRatioPart4` | `0.25` |
| `SeedsOsc2Vec12RMRatio` | `0.34375` |
| `SeedsOsc2Vec12SeedType` | `1` → Wave |
| `SeedsOsc2Vec12Transpose` | `0.5` |
| `SeedsOsc2Vec12VolPart1` | `1` |
| `SeedsOsc2Vec12VolPart2` | `0.875` |
| `SeedsOsc2Vec12VolPart3` | `0.75` |
| `SeedsOsc2Vec12VolPart4` | `0.625` |
| `SeedsOsc2Vec12Volume` | `0.7` |
| `SeedsOsc2Vec12Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc2Vec12WavetablePos` | `0.15` |
| `SeedsOsc2Vec12dirtReso` | `0` |
| `SeedsOsc2Vec12dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc2Vec1DirtType` | `0` → White Noise |
| `SeedsOsc2Vec1FMFeedback` | `0.1` |
| `SeedsOsc2Vec1FMIndex` | `0.35` |
| `SeedsOsc2Vec1FMRatio` | `0.3125` |
| `SeedsOsc2Vec1FreqRatioPart1` | `0.0625` |
| `SeedsOsc2Vec1FreqRatioPart2` | `0.125` |
| `SeedsOsc2Vec1FreqRatioPart3` | `0.1875` |
| `SeedsOsc2Vec1FreqRatioPart4` | `0.25` |
| `SeedsOsc2Vec1RMRatio` | `0.34375` |
| `SeedsOsc2Vec1SeedType` | `0` → Parts |
| `SeedsOsc2Vec1Transpose` | `0.5` |
| `SeedsOsc2Vec1VolPart1` | `1` |
| `SeedsOsc2Vec1VolPart2` | `0.875` |
| `SeedsOsc2Vec1VolPart3` | `0.75` |
| `SeedsOsc2Vec1VolPart4` | `0.625` |
| `SeedsOsc2Vec1Volume` | `0.7` |
| `SeedsOsc2Vec1Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc2Vec1WavetablePos` | `0.15` |
| `SeedsOsc2Vec1dirtReso` | `0` |
| `SeedsOsc2Vec1dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc2Vec2DirtType` | `0` → White Noise |
| `SeedsOsc2Vec2FMFeedback` | `0.1` |
| `SeedsOsc2Vec2FMIndex` | `0.35` |
| `SeedsOsc2Vec2FMRatio` | `0.3125` |
| `SeedsOsc2Vec2FreqRatioPart1` | `0.0625` |
| `SeedsOsc2Vec2FreqRatioPart2` | `0.125` |
| `SeedsOsc2Vec2FreqRatioPart3` | `0.1875` |
| `SeedsOsc2Vec2FreqRatioPart4` | `0.25` |
| `SeedsOsc2Vec2RMRatio` | `0.34375` |
| `SeedsOsc2Vec2SeedType` | `1` → Wave |
| `SeedsOsc2Vec2Transpose` | `0.5` |
| `SeedsOsc2Vec2VolPart1` | `1` |
| `SeedsOsc2Vec2VolPart2` | `0.875` |
| `SeedsOsc2Vec2VolPart3` | `0.75` |
| `SeedsOsc2Vec2VolPart4` | `0.625` |
| `SeedsOsc2Vec2Volume` | `0.7` |
| `SeedsOsc2Vec2Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc2Vec2WavetablePos` | `0.15` |
| `SeedsOsc2Vec2dirtReso` | `0` |
| `SeedsOsc2Vec2dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc2Vec3DirtType` | `0` → White Noise |
| `SeedsOsc2Vec3FMFeedback` | `0.1` |
| `SeedsOsc2Vec3FMIndex` | `0.35` |
| `SeedsOsc2Vec3FMRatio` | `0.3125` |
| `SeedsOsc2Vec3FreqRatioPart1` | `0.0625` |
| `SeedsOsc2Vec3FreqRatioPart2` | `0.125` |
| `SeedsOsc2Vec3FreqRatioPart3` | `0.1875` |
| `SeedsOsc2Vec3FreqRatioPart4` | `0.25` |
| `SeedsOsc2Vec3RMRatio` | `0.34375` |
| `SeedsOsc2Vec3SeedType` | `2` → FM |
| `SeedsOsc2Vec3Transpose` | `0.5` |
| `SeedsOsc2Vec3VolPart1` | `1` |
| `SeedsOsc2Vec3VolPart2` | `0.875` |
| `SeedsOsc2Vec3VolPart3` | `0.75` |
| `SeedsOsc2Vec3VolPart4` | `0.625` |
| `SeedsOsc2Vec3Volume` | `0.7` |
| `SeedsOsc2Vec3Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc2Vec3WavetablePos` | `0.15` |
| `SeedsOsc2Vec3dirtReso` | `0` |
| `SeedsOsc2Vec3dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc2Vec4DirtType` | `0` → White Noise |
| `SeedsOsc2Vec4FMFeedback` | `0.1` |
| `SeedsOsc2Vec4FMIndex` | `0.35` |
| `SeedsOsc2Vec4FMRatio` | `0.3125` |
| `SeedsOsc2Vec4FreqRatioPart1` | `0.0625` |
| `SeedsOsc2Vec4FreqRatioPart2` | `0.125` |
| `SeedsOsc2Vec4FreqRatioPart3` | `0.1875` |
| `SeedsOsc2Vec4FreqRatioPart4` | `0.25` |
| `SeedsOsc2Vec4RMRatio` | `0.34375` |
| `SeedsOsc2Vec4SeedType` | `3` → RM |
| `SeedsOsc2Vec4Transpose` | `0.5` |
| `SeedsOsc2Vec4VolPart1` | `1` |
| `SeedsOsc2Vec4VolPart2` | `0.875` |
| `SeedsOsc2Vec4VolPart3` | `0.75` |
| `SeedsOsc2Vec4VolPart4` | `0.625` |
| `SeedsOsc2Vec4Volume` | `0.7` |
| `SeedsOsc2Vec4Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc2Vec4WavetablePos` | `0.15` |
| `SeedsOsc2Vec4dirtReso` | `0` |
| `SeedsOsc2Vec4dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc2Vec5DirtType` | `0` → White Noise |
| `SeedsOsc2Vec5FMFeedback` | `0.1` |
| `SeedsOsc2Vec5FMIndex` | `0.35` |
| `SeedsOsc2Vec5FMRatio` | `0.3125` |
| `SeedsOsc2Vec5FreqRatioPart1` | `0.0625` |
| `SeedsOsc2Vec5FreqRatioPart2` | `0.125` |
| `SeedsOsc2Vec5FreqRatioPart3` | `0.1875` |
| `SeedsOsc2Vec5FreqRatioPart4` | `0.25` |
| `SeedsOsc2Vec5RMRatio` | `0.34375` |
| `SeedsOsc2Vec5SeedType` | `4` → Dirt |
| `SeedsOsc2Vec5Transpose` | `0.5` |
| `SeedsOsc2Vec5VolPart1` | `1` |
| `SeedsOsc2Vec5VolPart2` | `0.875` |
| `SeedsOsc2Vec5VolPart3` | `0.75` |
| `SeedsOsc2Vec5VolPart4` | `0.625` |
| `SeedsOsc2Vec5Volume` | `0.7` |
| `SeedsOsc2Vec5Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc2Vec5WavetablePos` | `0.15` |
| `SeedsOsc2Vec5dirtReso` | `0` |
| `SeedsOsc2Vec5dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc2Vec6DirtType` | `0` → White Noise |
| `SeedsOsc2Vec6FMFeedback` | `0.1` |
| `SeedsOsc2Vec6FMIndex` | `0.35` |
| `SeedsOsc2Vec6FMRatio` | `0.3125` |
| `SeedsOsc2Vec6FreqRatioPart1` | `0.0625` |
| `SeedsOsc2Vec6FreqRatioPart2` | `0.125` |
| `SeedsOsc2Vec6FreqRatioPart3` | `0.1875` |
| `SeedsOsc2Vec6FreqRatioPart4` | `0.25` |
| `SeedsOsc2Vec6RMRatio` | `0.34375` |
| `SeedsOsc2Vec6SeedType` | `0` → Parts |
| `SeedsOsc2Vec6Transpose` | `0.5` |
| `SeedsOsc2Vec6VolPart1` | `1` |
| `SeedsOsc2Vec6VolPart2` | `0.875` |
| `SeedsOsc2Vec6VolPart3` | `0.75` |
| `SeedsOsc2Vec6VolPart4` | `0.625` |
| `SeedsOsc2Vec6Volume` | `0.7` |
| `SeedsOsc2Vec6Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc2Vec6WavetablePos` | `0.15` |
| `SeedsOsc2Vec6dirtReso` | `0` |
| `SeedsOsc2Vec6dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc2Vec7DirtType` | `0` → White Noise |
| `SeedsOsc2Vec7FMFeedback` | `0.1` |
| `SeedsOsc2Vec7FMIndex` | `0.35` |
| `SeedsOsc2Vec7FMRatio` | `0.3125` |
| `SeedsOsc2Vec7FreqRatioPart1` | `0.0625` |
| `SeedsOsc2Vec7FreqRatioPart2` | `0.125` |
| `SeedsOsc2Vec7FreqRatioPart3` | `0.1875` |
| `SeedsOsc2Vec7FreqRatioPart4` | `0.25` |
| `SeedsOsc2Vec7RMRatio` | `0.34375` |
| `SeedsOsc2Vec7SeedType` | `1` → Wave |
| `SeedsOsc2Vec7Transpose` | `0.5` |
| `SeedsOsc2Vec7VolPart1` | `1` |
| `SeedsOsc2Vec7VolPart2` | `0.875` |
| `SeedsOsc2Vec7VolPart3` | `0.75` |
| `SeedsOsc2Vec7VolPart4` | `0.625` |
| `SeedsOsc2Vec7Volume` | `0.7` |
| `SeedsOsc2Vec7Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc2Vec7WavetablePos` | `0.15` |
| `SeedsOsc2Vec7dirtReso` | `0` |
| `SeedsOsc2Vec7dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc2Vec8DirtType` | `0` → White Noise |
| `SeedsOsc2Vec8FMFeedback` | `0.1` |
| `SeedsOsc2Vec8FMIndex` | `0.35` |
| `SeedsOsc2Vec8FMRatio` | `0.3125` |
| `SeedsOsc2Vec8FreqRatioPart1` | `0.0625` |
| `SeedsOsc2Vec8FreqRatioPart2` | `0.125` |
| `SeedsOsc2Vec8FreqRatioPart3` | `0.1875` |
| `SeedsOsc2Vec8FreqRatioPart4` | `0.25` |
| `SeedsOsc2Vec8RMRatio` | `0.34375` |
| `SeedsOsc2Vec8SeedType` | `2` → FM |
| `SeedsOsc2Vec8Transpose` | `0.5` |
| `SeedsOsc2Vec8VolPart1` | `1` |
| `SeedsOsc2Vec8VolPart2` | `0.875` |
| `SeedsOsc2Vec8VolPart3` | `0.75` |
| `SeedsOsc2Vec8VolPart4` | `0.625` |
| `SeedsOsc2Vec8Volume` | `0.7` |
| `SeedsOsc2Vec8Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc2Vec8WavetablePos` | `0.15` |
| `SeedsOsc2Vec8dirtReso` | `0` |
| `SeedsOsc2Vec8dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc2Vec9DirtType` | `0` → White Noise |
| `SeedsOsc2Vec9FMFeedback` | `0.1` |
| `SeedsOsc2Vec9FMIndex` | `0.35` |
| `SeedsOsc2Vec9FMRatio` | `0.3125` |
| `SeedsOsc2Vec9FreqRatioPart1` | `0.0625` |
| `SeedsOsc2Vec9FreqRatioPart2` | `0.125` |
| `SeedsOsc2Vec9FreqRatioPart3` | `0.1875` |
| `SeedsOsc2Vec9FreqRatioPart4` | `0.25` |
| `SeedsOsc2Vec9RMRatio` | `0.34375` |
| `SeedsOsc2Vec9SeedType` | `3` → RM |
| `SeedsOsc2Vec9Transpose` | `0.5` |
| `SeedsOsc2Vec9VolPart1` | `1` |
| `SeedsOsc2Vec9VolPart2` | `0.875` |
| `SeedsOsc2Vec9VolPart3` | `0.75` |
| `SeedsOsc2Vec9VolPart4` | `0.625` |
| `SeedsOsc2Vec9Volume` | `0.7` |
| `SeedsOsc2Vec9Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc2Vec9WavetablePos` | `0.15` |
| `SeedsOsc2Vec9dirtReso` | `0` |
| `SeedsOsc2Vec9dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc3Count` | `1` → 2 |
| `SeedsOsc3Detune` | `0.05` |
| `SeedsOsc3EnvAmount` | `0.5` |
| `SeedsOsc3NumVectors` | `4` → 5 |
| `SeedsOsc3Position` | `0` |
| `SeedsOsc3SoloVector` | `0` → 1 |
| `SeedsOsc3Spread` | `0.7` |
| `SeedsOsc3Vec10DirtType` | `0` → White Noise |
| `SeedsOsc3Vec10FMFeedback` | `0.1` |
| `SeedsOsc3Vec10FMIndex` | `0.35` |
| `SeedsOsc3Vec10FMRatio` | `0.3125` |
| `SeedsOsc3Vec10FreqRatioPart1` | `0.0625` |
| `SeedsOsc3Vec10FreqRatioPart2` | `0.125` |
| `SeedsOsc3Vec10FreqRatioPart3` | `0.1875` |
| `SeedsOsc3Vec10FreqRatioPart4` | `0.25` |
| `SeedsOsc3Vec10RMRatio` | `0.34375` |
| `SeedsOsc3Vec10SeedType` | `4` → Dirt |
| `SeedsOsc3Vec10Transpose` | `0.5` |
| `SeedsOsc3Vec10VolPart1` | `1` |
| `SeedsOsc3Vec10VolPart2` | `0.875` |
| `SeedsOsc3Vec10VolPart3` | `0.75` |
| `SeedsOsc3Vec10VolPart4` | `0.625` |
| `SeedsOsc3Vec10Volume` | `0.7` |
| `SeedsOsc3Vec10Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc3Vec10WavetablePos` | `0.15` |
| `SeedsOsc3Vec10dirtReso` | `0` |
| `SeedsOsc3Vec10dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc3Vec11DirtType` | `0` → White Noise |
| `SeedsOsc3Vec11FMFeedback` | `0.1` |
| `SeedsOsc3Vec11FMIndex` | `0.35` |
| `SeedsOsc3Vec11FMRatio` | `0.3125` |
| `SeedsOsc3Vec11FreqRatioPart1` | `0.0625` |
| `SeedsOsc3Vec11FreqRatioPart2` | `0.125` |
| `SeedsOsc3Vec11FreqRatioPart3` | `0.1875` |
| `SeedsOsc3Vec11FreqRatioPart4` | `0.25` |
| `SeedsOsc3Vec11RMRatio` | `0.34375` |
| `SeedsOsc3Vec11SeedType` | `0` → Parts |
| `SeedsOsc3Vec11Transpose` | `0.5` |
| `SeedsOsc3Vec11VolPart1` | `1` |
| `SeedsOsc3Vec11VolPart2` | `0.875` |
| `SeedsOsc3Vec11VolPart3` | `0.75` |
| `SeedsOsc3Vec11VolPart4` | `0.625` |
| `SeedsOsc3Vec11Volume` | `0.7` |
| `SeedsOsc3Vec11Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc3Vec11WavetablePos` | `0.15` |
| `SeedsOsc3Vec11dirtReso` | `0` |
| `SeedsOsc3Vec11dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc3Vec12DirtType` | `0` → White Noise |
| `SeedsOsc3Vec12FMFeedback` | `0.1` |
| `SeedsOsc3Vec12FMIndex` | `0.35` |
| `SeedsOsc3Vec12FMRatio` | `0.3125` |
| `SeedsOsc3Vec12FreqRatioPart1` | `0.0625` |
| `SeedsOsc3Vec12FreqRatioPart2` | `0.125` |
| `SeedsOsc3Vec12FreqRatioPart3` | `0.1875` |
| `SeedsOsc3Vec12FreqRatioPart4` | `0.25` |
| `SeedsOsc3Vec12RMRatio` | `0.34375` |
| `SeedsOsc3Vec12SeedType` | `1` → Wave |
| `SeedsOsc3Vec12Transpose` | `0.5` |
| `SeedsOsc3Vec12VolPart1` | `1` |
| `SeedsOsc3Vec12VolPart2` | `0.875` |
| `SeedsOsc3Vec12VolPart3` | `0.75` |
| `SeedsOsc3Vec12VolPart4` | `0.625` |
| `SeedsOsc3Vec12Volume` | `0.7` |
| `SeedsOsc3Vec12Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc3Vec12WavetablePos` | `0.15` |
| `SeedsOsc3Vec12dirtReso` | `0` |
| `SeedsOsc3Vec12dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc3Vec1DirtType` | `0` → White Noise |
| `SeedsOsc3Vec1FMFeedback` | `0.1` |
| `SeedsOsc3Vec1FMIndex` | `0.35` |
| `SeedsOsc3Vec1FMRatio` | `0.3125` |
| `SeedsOsc3Vec1FreqRatioPart1` | `0.0625` |
| `SeedsOsc3Vec1FreqRatioPart2` | `0.125` |
| `SeedsOsc3Vec1FreqRatioPart3` | `0.1875` |
| `SeedsOsc3Vec1FreqRatioPart4` | `0.25` |
| `SeedsOsc3Vec1RMRatio` | `0.34375` |
| `SeedsOsc3Vec1SeedType` | `0` → Parts |
| `SeedsOsc3Vec1Transpose` | `0.5` |
| `SeedsOsc3Vec1VolPart1` | `1` |
| `SeedsOsc3Vec1VolPart2` | `0.875` |
| `SeedsOsc3Vec1VolPart3` | `0.75` |
| `SeedsOsc3Vec1VolPart4` | `0.625` |
| `SeedsOsc3Vec1Volume` | `0.7` |
| `SeedsOsc3Vec1Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc3Vec1WavetablePos` | `0.15` |
| `SeedsOsc3Vec1dirtReso` | `0` |
| `SeedsOsc3Vec1dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc3Vec2DirtType` | `0` → White Noise |
| `SeedsOsc3Vec2FMFeedback` | `0.1` |
| `SeedsOsc3Vec2FMIndex` | `0.35` |
| `SeedsOsc3Vec2FMRatio` | `0.3125` |
| `SeedsOsc3Vec2FreqRatioPart1` | `0.0625` |
| `SeedsOsc3Vec2FreqRatioPart2` | `0.125` |
| `SeedsOsc3Vec2FreqRatioPart3` | `0.1875` |
| `SeedsOsc3Vec2FreqRatioPart4` | `0.25` |
| `SeedsOsc3Vec2RMRatio` | `0.34375` |
| `SeedsOsc3Vec2SeedType` | `1` → Wave |
| `SeedsOsc3Vec2Transpose` | `0.5` |
| `SeedsOsc3Vec2VolPart1` | `1` |
| `SeedsOsc3Vec2VolPart2` | `0.875` |
| `SeedsOsc3Vec2VolPart3` | `0.75` |
| `SeedsOsc3Vec2VolPart4` | `0.625` |
| `SeedsOsc3Vec2Volume` | `0.7` |
| `SeedsOsc3Vec2Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc3Vec2WavetablePos` | `0.15` |
| `SeedsOsc3Vec2dirtReso` | `0` |
| `SeedsOsc3Vec2dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc3Vec3DirtType` | `0` → White Noise |
| `SeedsOsc3Vec3FMFeedback` | `0.1` |
| `SeedsOsc3Vec3FMIndex` | `0.35` |
| `SeedsOsc3Vec3FMRatio` | `0.3125` |
| `SeedsOsc3Vec3FreqRatioPart1` | `0.0625` |
| `SeedsOsc3Vec3FreqRatioPart2` | `0.125` |
| `SeedsOsc3Vec3FreqRatioPart3` | `0.1875` |
| `SeedsOsc3Vec3FreqRatioPart4` | `0.25` |
| `SeedsOsc3Vec3RMRatio` | `0.34375` |
| `SeedsOsc3Vec3SeedType` | `2` → FM |
| `SeedsOsc3Vec3Transpose` | `0.5` |
| `SeedsOsc3Vec3VolPart1` | `1` |
| `SeedsOsc3Vec3VolPart2` | `0.875` |
| `SeedsOsc3Vec3VolPart3` | `0.75` |
| `SeedsOsc3Vec3VolPart4` | `0.625` |
| `SeedsOsc3Vec3Volume` | `0.7` |
| `SeedsOsc3Vec3Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc3Vec3WavetablePos` | `0.15` |
| `SeedsOsc3Vec3dirtReso` | `0` |
| `SeedsOsc3Vec3dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc3Vec4DirtType` | `0` → White Noise |
| `SeedsOsc3Vec4FMFeedback` | `0.1` |
| `SeedsOsc3Vec4FMIndex` | `0.35` |
| `SeedsOsc3Vec4FMRatio` | `0.3125` |
| `SeedsOsc3Vec4FreqRatioPart1` | `0.0625` |
| `SeedsOsc3Vec4FreqRatioPart2` | `0.125` |
| `SeedsOsc3Vec4FreqRatioPart3` | `0.1875` |
| `SeedsOsc3Vec4FreqRatioPart4` | `0.25` |
| `SeedsOsc3Vec4RMRatio` | `0.34375` |
| `SeedsOsc3Vec4SeedType` | `3` → RM |
| `SeedsOsc3Vec4Transpose` | `0.5` |
| `SeedsOsc3Vec4VolPart1` | `1` |
| `SeedsOsc3Vec4VolPart2` | `0.875` |
| `SeedsOsc3Vec4VolPart3` | `0.75` |
| `SeedsOsc3Vec4VolPart4` | `0.625` |
| `SeedsOsc3Vec4Volume` | `0.7` |
| `SeedsOsc3Vec4Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc3Vec4WavetablePos` | `0.15` |
| `SeedsOsc3Vec4dirtReso` | `0` |
| `SeedsOsc3Vec4dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc3Vec5DirtType` | `0` → White Noise |
| `SeedsOsc3Vec5FMFeedback` | `0.1` |
| `SeedsOsc3Vec5FMIndex` | `0.35` |
| `SeedsOsc3Vec5FMRatio` | `0.3125` |
| `SeedsOsc3Vec5FreqRatioPart1` | `0.0625` |
| `SeedsOsc3Vec5FreqRatioPart2` | `0.125` |
| `SeedsOsc3Vec5FreqRatioPart3` | `0.1875` |
| `SeedsOsc3Vec5FreqRatioPart4` | `0.25` |
| `SeedsOsc3Vec5RMRatio` | `0.34375` |
| `SeedsOsc3Vec5SeedType` | `4` → Dirt |
| `SeedsOsc3Vec5Transpose` | `0.5` |
| `SeedsOsc3Vec5VolPart1` | `1` |
| `SeedsOsc3Vec5VolPart2` | `0.875` |
| `SeedsOsc3Vec5VolPart3` | `0.75` |
| `SeedsOsc3Vec5VolPart4` | `0.625` |
| `SeedsOsc3Vec5Volume` | `0.7` |
| `SeedsOsc3Vec5Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc3Vec5WavetablePos` | `0.15` |
| `SeedsOsc3Vec5dirtReso` | `0` |
| `SeedsOsc3Vec5dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc3Vec6DirtType` | `0` → White Noise |
| `SeedsOsc3Vec6FMFeedback` | `0.1` |
| `SeedsOsc3Vec6FMIndex` | `0.35` |
| `SeedsOsc3Vec6FMRatio` | `0.3125` |
| `SeedsOsc3Vec6FreqRatioPart1` | `0.0625` |
| `SeedsOsc3Vec6FreqRatioPart2` | `0.125` |
| `SeedsOsc3Vec6FreqRatioPart3` | `0.1875` |
| `SeedsOsc3Vec6FreqRatioPart4` | `0.25` |
| `SeedsOsc3Vec6RMRatio` | `0.34375` |
| `SeedsOsc3Vec6SeedType` | `0` → Parts |
| `SeedsOsc3Vec6Transpose` | `0.5` |
| `SeedsOsc3Vec6VolPart1` | `1` |
| `SeedsOsc3Vec6VolPart2` | `0.875` |
| `SeedsOsc3Vec6VolPart3` | `0.75` |
| `SeedsOsc3Vec6VolPart4` | `0.625` |
| `SeedsOsc3Vec6Volume` | `0.7` |
| `SeedsOsc3Vec6Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc3Vec6WavetablePos` | `0.15` |
| `SeedsOsc3Vec6dirtReso` | `0` |
| `SeedsOsc3Vec6dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc3Vec7DirtType` | `0` → White Noise |
| `SeedsOsc3Vec7FMFeedback` | `0.1` |
| `SeedsOsc3Vec7FMIndex` | `0.35` |
| `SeedsOsc3Vec7FMRatio` | `0.3125` |
| `SeedsOsc3Vec7FreqRatioPart1` | `0.0625` |
| `SeedsOsc3Vec7FreqRatioPart2` | `0.125` |
| `SeedsOsc3Vec7FreqRatioPart3` | `0.1875` |
| `SeedsOsc3Vec7FreqRatioPart4` | `0.25` |
| `SeedsOsc3Vec7RMRatio` | `0.34375` |
| `SeedsOsc3Vec7SeedType` | `1` → Wave |
| `SeedsOsc3Vec7Transpose` | `0.5` |
| `SeedsOsc3Vec7VolPart1` | `1` |
| `SeedsOsc3Vec7VolPart2` | `0.875` |
| `SeedsOsc3Vec7VolPart3` | `0.75` |
| `SeedsOsc3Vec7VolPart4` | `0.625` |
| `SeedsOsc3Vec7Volume` | `0.7` |
| `SeedsOsc3Vec7Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc3Vec7WavetablePos` | `0.15` |
| `SeedsOsc3Vec7dirtReso` | `0` |
| `SeedsOsc3Vec7dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc3Vec8DirtType` | `0` → White Noise |
| `SeedsOsc3Vec8FMFeedback` | `0.1` |
| `SeedsOsc3Vec8FMIndex` | `0.35` |
| `SeedsOsc3Vec8FMRatio` | `0.3125` |
| `SeedsOsc3Vec8FreqRatioPart1` | `0.0625` |
| `SeedsOsc3Vec8FreqRatioPart2` | `0.125` |
| `SeedsOsc3Vec8FreqRatioPart3` | `0.1875` |
| `SeedsOsc3Vec8FreqRatioPart4` | `0.25` |
| `SeedsOsc3Vec8RMRatio` | `0.34375` |
| `SeedsOsc3Vec8SeedType` | `2` → FM |
| `SeedsOsc3Vec8Transpose` | `0.5` |
| `SeedsOsc3Vec8VolPart1` | `1` |
| `SeedsOsc3Vec8VolPart2` | `0.875` |
| `SeedsOsc3Vec8VolPart3` | `0.75` |
| `SeedsOsc3Vec8VolPart4` | `0.625` |
| `SeedsOsc3Vec8Volume` | `0.7` |
| `SeedsOsc3Vec8Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc3Vec8WavetablePos` | `0.15` |
| `SeedsOsc3Vec8dirtReso` | `0` |
| `SeedsOsc3Vec8dirtSpeed` | `0.25`; `0.5` |
| `SeedsOsc3Vec9DirtType` | `0` → White Noise |
| `SeedsOsc3Vec9FMFeedback` | `0.1` |
| `SeedsOsc3Vec9FMIndex` | `0.35` |
| `SeedsOsc3Vec9FMRatio` | `0.3125` |
| `SeedsOsc3Vec9FreqRatioPart1` | `0.0625` |
| `SeedsOsc3Vec9FreqRatioPart2` | `0.125` |
| `SeedsOsc3Vec9FreqRatioPart3` | `0.1875` |
| `SeedsOsc3Vec9FreqRatioPart4` | `0.25` |
| `SeedsOsc3Vec9RMRatio` | `0.34375` |
| `SeedsOsc3Vec9SeedType` | `3` → RM |
| `SeedsOsc3Vec9Transpose` | `0.5` |
| `SeedsOsc3Vec9VolPart1` | `1` |
| `SeedsOsc3Vec9VolPart2` | `0.875` |
| `SeedsOsc3Vec9VolPart3` | `0.75` |
| `SeedsOsc3Vec9VolPart4` | `0.625` |
| `SeedsOsc3Vec9Volume` | `0.7` |
| `SeedsOsc3Vec9Wavetable` | `49` → K+Strong 3 |
| `SeedsOsc3Vec9WavetablePos` | `0.15` |
| `SeedsOsc3Vec9dirtReso` | `0` |
| `SeedsOsc3Vec9dirtSpeed` | `0.25`; `0.5` |
| `SelectedColorItem` | `0` → LFOs |
| `SelectedColorVal` | `0` → Red |
| `SelectedMidiRow` | `0` → 0 |
| `SelectedSample` | `-1`; `0` → 1 |
| `SelectedSampleDirection` | `0` → Forward |
| `SelectedSampleEndPos` | `1` |
| `SelectedSampleF0` | `0.472441` |
| `SelectedSampleFromNote` | `0` → C-2 |
| `SelectedSampleFromVelo` | `0` → 0 |
| `SelectedSampleGain` | `0.1` |
| `SelectedSampleLoopEndPos` | `1` |
| `SelectedSampleLoopMode` | `0` → Off |
| `SelectedSampleLoopStartPos` | `0` |
| `SelectedSampleOsc` | `0` → 1; `1` → 2 |
| `SelectedSamplePan` | `0` |
| `SelectedSampleStartPos` | `0` |
| `SelectedSampleToNote` | `127` → G8 |
| `SelectedSampleToVelo` | `127` → 127 |
| `SelectedSampleTrackPitch` | `1` → Yes |
| `SelectedSampleXFade` | `0.1` |
| `SelectedSeedsOsc1Part` | `0` → 1 |
| `SelectedSeedsOsc1Vector` | `0` → 1 |
| `SelectedSeedsOsc2Part` | `0` → 1 |
| `SelectedSeedsOsc2Vector` | `0` → 1 |
| `SelectedSeedsOsc3Part` | `0` → 1 |
| `SelectedSeedsOsc3Vector` | `0` → 1 |
| `SelectedTest` | `0` → 0 |
| `SelectedWaveKF` | `0` → 1 |
| `SelectedWaveKFInterpol` | `0` → Linear |
| `SelectedWaveKFProcParam1` | `0` |
| `SelectedWaveKFProcParam2` | `0` |
| `SelectedWaveKFProcType` | `0` → Hard Sync |
| `SelectedWaveKFSpecAmp` | `0` |
| `SelectedWaveKFSpecBin` | `0` |
| `SelectedWaveKFType` | `0` → Wave |
| `SelectedWaveKFWaveType` | `0` → Sine |
| `SelectedWavetableOsc1Pos` | `0` |
| `SelectedWavetableOsc2Pos` | `0` |
| `SelectedWavetableOsc3Pos` | `0` |
| `SendsAux` | `0` → Off |
| `SendsMain` | `1` → On |
| `SeqDirection` | `0` → Forward |
| `SeqLength` | `7` → 8; `15` → 16 |
| `SeqResetMode` | `0` → First Step |
| `SeqScale` | `0` → Chromatic |
| `SeqScaleRoot` | `0` → Transpose |
| `SeqSelStep` | `0` → 1 |
| `SeqStep10Gate` | `0.5`; `1` |
| `SeqStep10Param1` | `0`; `0.5` |
| `SeqStep10Param2` | `0`; `0.5` |
| `SeqStep10Param3` | `0`; `0.5` |
| `SeqStep10Param4` | `0`; `0.5` |
| `SeqStep10Param5` | `0.5` |
| `SeqStep10Param6` | `0.5` |
| `SeqStep10Param7` | `0.5` |
| `SeqStep10Param8` | `0.5` |
| `SeqStep10Pitch` | `24` → +0 |
| `SeqStep10Type` | `0` |
| `SeqStep10Velo` | `0.8`; `1` |
| `SeqStep11Gate` | `0.5`; `1` |
| `SeqStep11Param1` | `0`; `0.5` |
| `SeqStep11Param2` | `0`; `0.5` |
| `SeqStep11Param3` | `0`; `0.5` |
| `SeqStep11Param4` | `0`; `0.5` |
| `SeqStep11Param5` | `0.5` |
| `SeqStep11Param6` | `0.5` |
| `SeqStep11Param7` | `0.5` |
| `SeqStep11Param8` | `0.5` |
| `SeqStep11Pitch` | `24` → +0 |
| `SeqStep11Type` | `0` |
| `SeqStep11Velo` | `0.8`; `1` |
| `SeqStep12Gate` | `0.5`; `1` |
| `SeqStep12Param1` | `0`; `0.5` |
| `SeqStep12Param2` | `0`; `0.5` |
| `SeqStep12Param3` | `0`; `0.5` |
| `SeqStep12Param4` | `0`; `0.5` |
| `SeqStep12Param5` | `0.5` |
| `SeqStep12Param6` | `0.5` |
| `SeqStep12Param7` | `0.5` |
| `SeqStep12Param8` | `0.5` |
| `SeqStep12Pitch` | `24` → +0 |
| `SeqStep12Type` | `0` |
| `SeqStep12Velo` | `0.8`; `1` |
| `SeqStep13Gate` | `0.5`; `1` |
| `SeqStep13Param1` | `0`; `0.5` |
| `SeqStep13Param2` | `0`; `0.5` |
| `SeqStep13Param3` | `0`; `0.5` |
| `SeqStep13Param4` | `0`; `0.5` |
| `SeqStep13Param5` | `0.5` |
| `SeqStep13Param6` | `0.5` |
| `SeqStep13Param7` | `0.5` |
| `SeqStep13Param8` | `0.5` |
| `SeqStep13Pitch` | `24` → +0 |
| `SeqStep13Type` | `0` |
| `SeqStep13Velo` | `0.8`; `1` |
| `SeqStep14Gate` | `0.5`; `1` |
| `SeqStep14Param1` | `0`; `0.5` |
| `SeqStep14Param2` | `0`; `0.5` |
| `SeqStep14Param3` | `0`; `0.5` |
| `SeqStep14Param4` | `0`; `0.5` |
| `SeqStep14Param5` | `0.5` |
| `SeqStep14Param6` | `0.5` |
| `SeqStep14Param7` | `0.5` |
| `SeqStep14Param8` | `0.5` |
| `SeqStep14Pitch` | `24` → +0 |
| `SeqStep14Type` | `0` |
| `SeqStep14Velo` | `0.8`; `1` |
| `SeqStep15Gate` | `0.5`; `1` |
| `SeqStep15Param1` | `0`; `0.5` |
| `SeqStep15Param2` | `0`; `0.5` |
| `SeqStep15Param3` | `0`; `0.5` |
| `SeqStep15Param4` | `0`; `0.5` |
| `SeqStep15Param5` | `0.5` |
| `SeqStep15Param6` | `0.5` |
| `SeqStep15Param7` | `0.5` |
| `SeqStep15Param8` | `0.5` |
| `SeqStep15Pitch` | `24` → +0 |
| `SeqStep15Type` | `0` |
| `SeqStep15Velo` | `0.8`; `1` |
| `SeqStep16Gate` | `0.5`; `1` |
| `SeqStep16Param1` | `0`; `0.5` |
| `SeqStep16Param2` | `0`; `0.5` |
| `SeqStep16Param3` | `0`; `0.5` |
| `SeqStep16Param4` | `0`; `0.5` |
| `SeqStep16Param5` | `0.5` |
| `SeqStep16Param6` | `0.5` |
| `SeqStep16Param7` | `0.5` |
| `SeqStep16Param8` | `0.5` |
| `SeqStep16Pitch` | `24` → +0 |
| `SeqStep16Type` | `0` |
| `SeqStep16Velo` | `0.8`; `1` |
| `SeqStep17Gate` | `0.5`; `1` |
| `SeqStep17Param1` | `0`; `0.5` |
| `SeqStep17Param2` | `0`; `0.5` |
| `SeqStep17Param3` | `0`; `0.5` |
| `SeqStep17Param4` | `0`; `0.5` |
| `SeqStep17Param5` | `0.5` |
| `SeqStep17Param6` | `0.5` |
| `SeqStep17Param7` | `0.5` |
| `SeqStep17Param8` | `0.5` |
| `SeqStep17Pitch` | `24` → +0 |
| `SeqStep17Type` | `0` |
| `SeqStep17Velo` | `0.8`; `1` |
| `SeqStep18Gate` | `0.5`; `1` |
| `SeqStep18Param1` | `0`; `0.5` |
| `SeqStep18Param2` | `0`; `0.5` |
| `SeqStep18Param3` | `0`; `0.5` |
| `SeqStep18Param4` | `0`; `0.5` |
| `SeqStep18Param5` | `0.5` |
| `SeqStep18Param6` | `0.5` |
| `SeqStep18Param7` | `0.5` |
| `SeqStep18Param8` | `0.5` |
| `SeqStep18Pitch` | `24` → +0 |
| `SeqStep18Type` | `0` |
| `SeqStep18Velo` | `0.8`; `1` |
| `SeqStep19Gate` | `0.5`; `1` |
| `SeqStep19Param1` | `0`; `0.5` |
| `SeqStep19Param2` | `0`; `0.5` |
| `SeqStep19Param3` | `0`; `0.5` |
| `SeqStep19Param4` | `0`; `0.5` |
| `SeqStep19Param5` | `0.5` |
| `SeqStep19Param6` | `0.5` |
| `SeqStep19Param7` | `0.5` |
| `SeqStep19Param8` | `0.5` |
| `SeqStep19Pitch` | `24` → +0 |
| `SeqStep19Type` | `0` |
| `SeqStep19Velo` | `0.8`; `1` |
| `SeqStep1Gate` | `0.5`; `1` |
| `SeqStep1Param1` | `0`; `0.5` |
| `SeqStep1Param2` | `0`; `0.5` |
| `SeqStep1Param3` | `0`; `0.5` |
| `SeqStep1Param4` | `0`; `0.5` |
| `SeqStep1Param5` | `0.5` |
| `SeqStep1Param6` | `0.5` |
| `SeqStep1Param7` | `0.5` |
| `SeqStep1Param8` | `0.5` |
| `SeqStep1Pitch` | `24` → +0 |
| `SeqStep1Type` | `0` |
| `SeqStep1Velo` | `0.8`; `1` |
| `SeqStep20Gate` | `0.5`; `1` |
| `SeqStep20Param1` | `0`; `0.5` |
| `SeqStep20Param2` | `0`; `0.5` |
| `SeqStep20Param3` | `0`; `0.5` |
| `SeqStep20Param4` | `0`; `0.5` |
| `SeqStep20Param5` | `0.5` |
| `SeqStep20Param6` | `0.5` |
| `SeqStep20Param7` | `0.5` |
| `SeqStep20Param8` | `0.5` |
| `SeqStep20Pitch` | `24` → +0 |
| `SeqStep20Type` | `0` |
| `SeqStep20Velo` | `0.8`; `1` |
| `SeqStep21Gate` | `0.5`; `1` |
| `SeqStep21Param1` | `0`; `0.5` |
| `SeqStep21Param2` | `0`; `0.5` |
| `SeqStep21Param3` | `0`; `0.5` |
| `SeqStep21Param4` | `0`; `0.5` |
| `SeqStep21Param5` | `0.5` |
| `SeqStep21Param6` | `0.5` |
| `SeqStep21Param7` | `0.5` |
| `SeqStep21Param8` | `0.5` |
| `SeqStep21Pitch` | `24` → +0 |
| `SeqStep21Type` | `0` |
| `SeqStep21Velo` | `0.8`; `1` |
| `SeqStep22Gate` | `0.5`; `1` |
| `SeqStep22Param1` | `0`; `0.5` |
| `SeqStep22Param2` | `0`; `0.5` |
| `SeqStep22Param3` | `0`; `0.5` |
| `SeqStep22Param4` | `0`; `0.5` |
| `SeqStep22Param5` | `0.5` |
| `SeqStep22Param6` | `0.5` |
| `SeqStep22Param7` | `0.5` |
| `SeqStep22Param8` | `0.5` |
| `SeqStep22Pitch` | `24` → +0 |
| `SeqStep22Type` | `0` |
| `SeqStep22Velo` | `0.8`; `1` |
| `SeqStep23Gate` | `0.5`; `1` |
| `SeqStep23Param1` | `0`; `0.5` |
| `SeqStep23Param2` | `0`; `0.5` |
| `SeqStep23Param3` | `0`; `0.5` |
| `SeqStep23Param4` | `0`; `0.5` |
| `SeqStep23Param5` | `0.5` |
| `SeqStep23Param6` | `0.5` |
| `SeqStep23Param7` | `0.5` |
| `SeqStep23Param8` | `0.5` |
| `SeqStep23Pitch` | `24` → +0 |
| `SeqStep23Type` | `0` |
| `SeqStep23Velo` | `0.8`; `1` |
| `SeqStep24Gate` | `0.5`; `1` |
| `SeqStep24Param1` | `0`; `0.5` |
| `SeqStep24Param2` | `0`; `0.5` |
| `SeqStep24Param3` | `0`; `0.5` |
| `SeqStep24Param4` | `0`; `0.5` |
| `SeqStep24Param5` | `0.5` |
| `SeqStep24Param6` | `0.5` |
| `SeqStep24Param7` | `0.5` |
| `SeqStep24Param8` | `0.5` |
| `SeqStep24Pitch` | `24` → +0 |
| `SeqStep24Type` | `0` |
| `SeqStep24Velo` | `0.8`; `1` |
| `SeqStep25Gate` | `0.5`; `1` |
| `SeqStep25Param1` | `0`; `0.5` |
| `SeqStep25Param2` | `0`; `0.5` |
| `SeqStep25Param3` | `0`; `0.5` |
| `SeqStep25Param4` | `0`; `0.5` |
| `SeqStep25Param5` | `0.5` |
| `SeqStep25Param6` | `0.5` |
| `SeqStep25Param7` | `0.5` |
| `SeqStep25Param8` | `0.5` |
| `SeqStep25Pitch` | `24` → +0 |
| `SeqStep25Type` | `0` |
| `SeqStep25Velo` | `0.8`; `1` |
| `SeqStep26Gate` | `0.5`; `1` |
| `SeqStep26Param1` | `0`; `0.5` |
| `SeqStep26Param2` | `0`; `0.5` |
| `SeqStep26Param3` | `0`; `0.5` |
| `SeqStep26Param4` | `0`; `0.5` |
| `SeqStep26Param5` | `0.5` |
| `SeqStep26Param6` | `0.5` |
| `SeqStep26Param7` | `0.5` |
| `SeqStep26Param8` | `0.5` |
| `SeqStep26Pitch` | `24` → +0 |
| `SeqStep26Type` | `0` |
| `SeqStep26Velo` | `0.8`; `1` |
| `SeqStep27Gate` | `0.5`; `1` |
| `SeqStep27Param1` | `0`; `0.5` |
| `SeqStep27Param2` | `0`; `0.5` |
| `SeqStep27Param3` | `0`; `0.5` |
| `SeqStep27Param4` | `0`; `0.5` |
| `SeqStep27Param5` | `0.5` |
| `SeqStep27Param6` | `0.5` |
| `SeqStep27Param7` | `0.5` |
| `SeqStep27Param8` | `0.5` |
| `SeqStep27Pitch` | `24` → +0 |
| `SeqStep27Type` | `0` |
| `SeqStep27Velo` | `0.8`; `1` |
| `SeqStep28Gate` | `0.5`; `1` |
| `SeqStep28Param1` | `0`; `0.5` |
| `SeqStep28Param2` | `0`; `0.5` |
| `SeqStep28Param3` | `0`; `0.5` |
| `SeqStep28Param4` | `0`; `0.5` |
| `SeqStep28Param5` | `0.5` |
| `SeqStep28Param6` | `0.5` |
| `SeqStep28Param7` | `0.5` |
| `SeqStep28Param8` | `0.5` |
| `SeqStep28Pitch` | `24` → +0 |
| `SeqStep28Type` | `0` |
| `SeqStep28Velo` | `0.8`; `1` |
| `SeqStep29Gate` | `0.5`; `1` |
| `SeqStep29Param1` | `0`; `0.5` |
| `SeqStep29Param2` | `0`; `0.5` |
| `SeqStep29Param3` | `0`; `0.5` |
| `SeqStep29Param4` | `0`; `0.5` |
| `SeqStep29Param5` | `0.5` |
| `SeqStep29Param6` | `0.5` |
| `SeqStep29Param7` | `0.5` |
| `SeqStep29Param8` | `0.5` |
| `SeqStep29Pitch` | `24` → +0 |
| `SeqStep29Type` | `0` |
| `SeqStep29Velo` | `0.8`; `1` |
| `SeqStep2Gate` | `0.5`; `1` |
| `SeqStep2Param1` | `0`; `0.5` |
| `SeqStep2Param2` | `0`; `0.5` |
| `SeqStep2Param3` | `0`; `0.5` |
| `SeqStep2Param4` | `0`; `0.5` |
| `SeqStep2Param5` | `0.5` |
| `SeqStep2Param6` | `0.5` |
| `SeqStep2Param7` | `0.5` |
| `SeqStep2Param8` | `0.5` |
| `SeqStep2Pitch` | `24` → +0 |
| `SeqStep2Type` | `0` |
| `SeqStep2Velo` | `0.8`; `1` |
| `SeqStep30Gate` | `0.5`; `1` |
| `SeqStep30Param1` | `0`; `0.5` |
| `SeqStep30Param2` | `0`; `0.5` |
| `SeqStep30Param3` | `0`; `0.5` |
| `SeqStep30Param4` | `0`; `0.5` |
| `SeqStep30Param5` | `0.5` |
| `SeqStep30Param6` | `0.5` |
| `SeqStep30Param7` | `0.5` |
| `SeqStep30Param8` | `0.5` |
| `SeqStep30Pitch` | `24` → +0 |
| `SeqStep30Type` | `0` |
| `SeqStep30Velo` | `0.8`; `1` |
| `SeqStep31Gate` | `0.5`; `1` |
| `SeqStep31Param1` | `0`; `0.5` |
| `SeqStep31Param2` | `0`; `0.5` |
| `SeqStep31Param3` | `0`; `0.5` |
| `SeqStep31Param4` | `0`; `0.5` |
| `SeqStep31Param5` | `0.5` |
| `SeqStep31Param6` | `0.5` |
| `SeqStep31Param7` | `0.5` |
| `SeqStep31Param8` | `0.5` |
| `SeqStep31Pitch` | `24` → +0 |
| `SeqStep31Type` | `0` |
| `SeqStep31Velo` | `0.8`; `1` |
| `SeqStep32Gate` | `0.5`; `1` |
| `SeqStep32Param1` | `0`; `0.5` |
| `SeqStep32Param2` | `0`; `0.5` |
| `SeqStep32Param3` | `0`; `0.5` |
| `SeqStep32Param4` | `0`; `0.5` |
| `SeqStep32Param5` | `0.5` |
| `SeqStep32Param6` | `0.5` |
| `SeqStep32Param7` | `0.5` |
| `SeqStep32Param8` | `0.5` |
| `SeqStep32Pitch` | `24` → +0 |
| `SeqStep32Type` | `0` |
| `SeqStep32Velo` | `0.8`; `1` |
| `SeqStep33Gate` | `1` |
| `SeqStep33Param1` | `0.5` |
| `SeqStep33Param2` | `0.5` |
| `SeqStep33Param3` | `0.5` |
| `SeqStep33Param4` | `0.5` |
| `SeqStep33Param5` | `0.5` |
| `SeqStep33Param6` | `0.5` |
| `SeqStep33Param7` | `0.5` |
| `SeqStep33Param8` | `0.5` |
| `SeqStep33Pitch` | `24` → +0 |
| `SeqStep33Type` | `0` |
| `SeqStep33Velo` | `0.8` |
| `SeqStep34Gate` | `1` |
| `SeqStep34Param1` | `0.5` |
| `SeqStep34Param2` | `0.5` |
| `SeqStep34Param3` | `0.5` |
| `SeqStep34Param4` | `0.5` |
| `SeqStep34Param5` | `0.5` |
| `SeqStep34Param6` | `0.5` |
| `SeqStep34Param7` | `0.5` |
| `SeqStep34Param8` | `0.5` |
| `SeqStep34Pitch` | `24` → +0 |
| `SeqStep34Type` | `0` |
| `SeqStep34Velo` | `0.8` |
| `SeqStep35Gate` | `1` |
| `SeqStep35Param1` | `0.5` |
| `SeqStep35Param2` | `0.5` |
| `SeqStep35Param3` | `0.5` |
| `SeqStep35Param4` | `0.5` |
| `SeqStep35Param5` | `0.5` |
| `SeqStep35Param6` | `0.5` |
| `SeqStep35Param7` | `0.5` |
| `SeqStep35Param8` | `0.5` |
| `SeqStep35Pitch` | `24` → +0 |
| `SeqStep35Type` | `0` |
| `SeqStep35Velo` | `0.8` |
| `SeqStep36Gate` | `1` |
| `SeqStep36Param1` | `0.5` |
| `SeqStep36Param2` | `0.5` |
| `SeqStep36Param3` | `0.5` |
| `SeqStep36Param4` | `0.5` |
| `SeqStep36Param5` | `0.5` |
| `SeqStep36Param6` | `0.5` |
| `SeqStep36Param7` | `0.5` |
| `SeqStep36Param8` | `0.5` |
| `SeqStep36Pitch` | `24` → +0 |
| `SeqStep36Type` | `0` |
| `SeqStep36Velo` | `0.8` |
| `SeqStep37Gate` | `1` |
| `SeqStep37Param1` | `0.5` |
| `SeqStep37Param2` | `0.5` |
| `SeqStep37Param3` | `0.5` |
| `SeqStep37Param4` | `0.5` |
| `SeqStep37Param5` | `0.5` |
| `SeqStep37Param6` | `0.5` |
| `SeqStep37Param7` | `0.5` |
| `SeqStep37Param8` | `0.5` |
| `SeqStep37Pitch` | `24` → +0 |
| `SeqStep37Type` | `0` |
| `SeqStep37Velo` | `0.8` |
| `SeqStep38Gate` | `1` |
| `SeqStep38Param1` | `0.5` |
| `SeqStep38Param2` | `0.5` |
| `SeqStep38Param3` | `0.5` |
| `SeqStep38Param4` | `0.5` |
| `SeqStep38Param5` | `0.5` |
| `SeqStep38Param6` | `0.5` |
| `SeqStep38Param7` | `0.5` |
| `SeqStep38Param8` | `0.5` |
| `SeqStep38Pitch` | `24` → +0 |
| `SeqStep38Type` | `0` |
| `SeqStep38Velo` | `0.8` |
| `SeqStep39Gate` | `1` |
| `SeqStep39Param1` | `0.5` |
| `SeqStep39Param2` | `0.5` |
| `SeqStep39Param3` | `0.5` |
| `SeqStep39Param4` | `0.5` |
| `SeqStep39Param5` | `0.5` |
| `SeqStep39Param6` | `0.5` |
| `SeqStep39Param7` | `0.5` |
| `SeqStep39Param8` | `0.5` |
| `SeqStep39Pitch` | `24` → +0 |
| `SeqStep39Type` | `0` |
| `SeqStep39Velo` | `0.8` |
| `SeqStep3Gate` | `0.5`; `1` |
| `SeqStep3Param1` | `0`; `0.5` |
| `SeqStep3Param2` | `0`; `0.5` |
| `SeqStep3Param3` | `0`; `0.5` |
| `SeqStep3Param4` | `0`; `0.5` |
| `SeqStep3Param5` | `0.5` |
| `SeqStep3Param6` | `0.5` |
| `SeqStep3Param7` | `0.5` |
| `SeqStep3Param8` | `0.5` |
| `SeqStep3Pitch` | `24` → +0 |
| `SeqStep3Type` | `0` |
| `SeqStep3Velo` | `0.8`; `1` |
| `SeqStep40Gate` | `1` |
| `SeqStep40Param1` | `0.5` |
| `SeqStep40Param2` | `0.5` |
| `SeqStep40Param3` | `0.5` |
| `SeqStep40Param4` | `0.5` |
| `SeqStep40Param5` | `0.5` |
| `SeqStep40Param6` | `0.5` |
| `SeqStep40Param7` | `0.5` |
| `SeqStep40Param8` | `0.5` |
| `SeqStep40Pitch` | `24` → +0 |
| `SeqStep40Type` | `0` |
| `SeqStep40Velo` | `0.8` |
| `SeqStep41Gate` | `1` |
| `SeqStep41Param1` | `0.5` |
| `SeqStep41Param2` | `0.5` |
| `SeqStep41Param3` | `0.5` |
| `SeqStep41Param4` | `0.5` |
| `SeqStep41Param5` | `0.5` |
| `SeqStep41Param6` | `0.5` |
| `SeqStep41Param7` | `0.5` |
| `SeqStep41Param8` | `0.5` |
| `SeqStep41Pitch` | `24` → +0 |
| `SeqStep41Type` | `0` |
| `SeqStep41Velo` | `0.8` |
| `SeqStep42Gate` | `1` |
| `SeqStep42Param1` | `0.5` |
| `SeqStep42Param2` | `0.5` |
| `SeqStep42Param3` | `0.5` |
| `SeqStep42Param4` | `0.5` |
| `SeqStep42Param5` | `0.5` |
| `SeqStep42Param6` | `0.5` |
| `SeqStep42Param7` | `0.5` |
| `SeqStep42Param8` | `0.5` |
| `SeqStep42Pitch` | `24` → +0 |
| `SeqStep42Type` | `0` |
| `SeqStep42Velo` | `0.8` |
| `SeqStep43Gate` | `1` |
| `SeqStep43Param1` | `0.5` |
| `SeqStep43Param2` | `0.5` |
| `SeqStep43Param3` | `0.5` |
| `SeqStep43Param4` | `0.5` |
| `SeqStep43Param5` | `0.5` |
| `SeqStep43Param6` | `0.5` |
| `SeqStep43Param7` | `0.5` |
| `SeqStep43Param8` | `0.5` |
| `SeqStep43Pitch` | `24` → +0 |
| `SeqStep43Type` | `0` |
| `SeqStep43Velo` | `0.8` |
| `SeqStep44Gate` | `1` |
| `SeqStep44Param1` | `0.5` |
| `SeqStep44Param2` | `0.5` |
| `SeqStep44Param3` | `0.5` |
| `SeqStep44Param4` | `0.5` |
| `SeqStep44Param5` | `0.5` |
| `SeqStep44Param6` | `0.5` |
| `SeqStep44Param7` | `0.5` |
| `SeqStep44Param8` | `0.5` |
| `SeqStep44Pitch` | `24` → +0 |
| `SeqStep44Type` | `0` |
| `SeqStep44Velo` | `0.8` |
| `SeqStep45Gate` | `1` |
| `SeqStep45Param1` | `0.5` |
| `SeqStep45Param2` | `0.5` |
| `SeqStep45Param3` | `0.5` |
| `SeqStep45Param4` | `0.5` |
| `SeqStep45Param5` | `0.5` |
| `SeqStep45Param6` | `0.5` |
| `SeqStep45Param7` | `0.5` |
| `SeqStep45Param8` | `0.5` |
| `SeqStep45Pitch` | `24` → +0 |
| `SeqStep45Type` | `0` |
| `SeqStep45Velo` | `0.8` |
| `SeqStep46Gate` | `1` |
| `SeqStep46Param1` | `0.5` |
| `SeqStep46Param2` | `0.5` |
| `SeqStep46Param3` | `0.5` |
| `SeqStep46Param4` | `0.5` |
| `SeqStep46Param5` | `0.5` |
| `SeqStep46Param6` | `0.5` |
| `SeqStep46Param7` | `0.5` |
| `SeqStep46Param8` | `0.5` |
| `SeqStep46Pitch` | `24` → +0 |
| `SeqStep46Type` | `0` |
| `SeqStep46Velo` | `0.8` |
| `SeqStep47Gate` | `1` |
| `SeqStep47Param1` | `0.5` |
| `SeqStep47Param2` | `0.5` |
| `SeqStep47Param3` | `0.5` |
| `SeqStep47Param4` | `0.5` |
| `SeqStep47Param5` | `0.5` |
| `SeqStep47Param6` | `0.5` |
| `SeqStep47Param7` | `0.5` |
| `SeqStep47Param8` | `0.5` |
| `SeqStep47Pitch` | `24` → +0 |
| `SeqStep47Type` | `0` |
| `SeqStep47Velo` | `0.8` |
| `SeqStep48Gate` | `1` |
| `SeqStep48Param1` | `0.5` |
| `SeqStep48Param2` | `0.5` |
| `SeqStep48Param3` | `0.5` |
| `SeqStep48Param4` | `0.5` |
| `SeqStep48Param5` | `0.5` |
| `SeqStep48Param6` | `0.5` |
| `SeqStep48Param7` | `0.5` |
| `SeqStep48Param8` | `0.5` |
| `SeqStep48Pitch` | `24` → +0 |
| `SeqStep48Type` | `0` |
| `SeqStep48Velo` | `0.8` |
| `SeqStep49Gate` | `1` |
| `SeqStep49Param1` | `0.5` |
| `SeqStep49Param2` | `0.5` |
| `SeqStep49Param3` | `0.5` |
| `SeqStep49Param4` | `0.5` |
| `SeqStep49Param5` | `0.5` |
| `SeqStep49Param6` | `0.5` |
| `SeqStep49Param7` | `0.5` |
| `SeqStep49Param8` | `0.5` |
| `SeqStep49Pitch` | `24` → +0 |
| `SeqStep49Type` | `0` |
| `SeqStep49Velo` | `0.8` |
| `SeqStep4Gate` | `0.5`; `1` |
| `SeqStep4Param1` | `0`; `0.5` |
| `SeqStep4Param2` | `0`; `0.5` |
| `SeqStep4Param3` | `0`; `0.5` |
| `SeqStep4Param4` | `0`; `0.5` |
| `SeqStep4Param5` | `0.5` |
| `SeqStep4Param6` | `0.5` |
| `SeqStep4Param7` | `0.5` |
| `SeqStep4Param8` | `0.5` |
| `SeqStep4Pitch` | `24` → +0 |
| `SeqStep4Type` | `0` |
| `SeqStep4Velo` | `0.8`; `1` |
| `SeqStep50Gate` | `1` |
| `SeqStep50Param1` | `0.5` |
| `SeqStep50Param2` | `0.5` |
| `SeqStep50Param3` | `0.5` |
| `SeqStep50Param4` | `0.5` |
| `SeqStep50Param5` | `0.5` |
| `SeqStep50Param6` | `0.5` |
| `SeqStep50Param7` | `0.5` |
| `SeqStep50Param8` | `0.5` |
| `SeqStep50Pitch` | `24` → +0 |
| `SeqStep50Type` | `0` |
| `SeqStep50Velo` | `0.8` |
| `SeqStep51Gate` | `1` |
| `SeqStep51Param1` | `0.5` |
| `SeqStep51Param2` | `0.5` |
| `SeqStep51Param3` | `0.5` |
| `SeqStep51Param4` | `0.5` |
| `SeqStep51Param5` | `0.5` |
| `SeqStep51Param6` | `0.5` |
| `SeqStep51Param7` | `0.5` |
| `SeqStep51Param8` | `0.5` |
| `SeqStep51Pitch` | `24` → +0 |
| `SeqStep51Type` | `0` |
| `SeqStep51Velo` | `0.8` |
| `SeqStep52Gate` | `1` |
| `SeqStep52Param1` | `0.5` |
| `SeqStep52Param2` | `0.5` |
| `SeqStep52Param3` | `0.5` |
| `SeqStep52Param4` | `0.5` |
| `SeqStep52Param5` | `0.5` |
| `SeqStep52Param6` | `0.5` |
| `SeqStep52Param7` | `0.5` |
| `SeqStep52Param8` | `0.5` |
| `SeqStep52Pitch` | `24` → +0 |
| `SeqStep52Type` | `0` |
| `SeqStep52Velo` | `0.8` |
| `SeqStep53Gate` | `1` |
| `SeqStep53Param1` | `0.5` |
| `SeqStep53Param2` | `0.5` |
| `SeqStep53Param3` | `0.5` |
| `SeqStep53Param4` | `0.5` |
| `SeqStep53Param5` | `0.5` |
| `SeqStep53Param6` | `0.5` |
| `SeqStep53Param7` | `0.5` |
| `SeqStep53Param8` | `0.5` |
| `SeqStep53Pitch` | `24` → +0 |
| `SeqStep53Type` | `0` |
| `SeqStep53Velo` | `0.8` |
| `SeqStep54Gate` | `1` |
| `SeqStep54Param1` | `0.5` |
| `SeqStep54Param2` | `0.5` |
| `SeqStep54Param3` | `0.5` |
| `SeqStep54Param4` | `0.5` |
| `SeqStep54Param5` | `0.5` |
| `SeqStep54Param6` | `0.5` |
| `SeqStep54Param7` | `0.5` |
| `SeqStep54Param8` | `0.5` |
| `SeqStep54Pitch` | `24` → +0 |
| `SeqStep54Type` | `0` |
| `SeqStep54Velo` | `0.8` |
| `SeqStep55Gate` | `1` |
| `SeqStep55Param1` | `0.5` |
| `SeqStep55Param2` | `0.5` |
| `SeqStep55Param3` | `0.5` |
| `SeqStep55Param4` | `0.5` |
| `SeqStep55Param5` | `0.5` |
| `SeqStep55Param6` | `0.5` |
| `SeqStep55Param7` | `0.5` |
| `SeqStep55Param8` | `0.5` |
| `SeqStep55Pitch` | `24` → +0 |
| `SeqStep55Type` | `0` |
| `SeqStep55Velo` | `0.8` |
| `SeqStep56Gate` | `1` |
| `SeqStep56Param1` | `0.5` |
| `SeqStep56Param2` | `0.5` |
| `SeqStep56Param3` | `0.5` |
| `SeqStep56Param4` | `0.5` |
| `SeqStep56Param5` | `0.5` |
| `SeqStep56Param6` | `0.5` |
| `SeqStep56Param7` | `0.5` |
| `SeqStep56Param8` | `0.5` |
| `SeqStep56Pitch` | `24` → +0 |
| `SeqStep56Type` | `0` |
| `SeqStep56Velo` | `0.8` |
| `SeqStep57Gate` | `1` |
| `SeqStep57Param1` | `0.5` |
| `SeqStep57Param2` | `0.5` |
| `SeqStep57Param3` | `0.5` |
| `SeqStep57Param4` | `0.5` |
| `SeqStep57Param5` | `0.5` |
| `SeqStep57Param6` | `0.5` |
| `SeqStep57Param7` | `0.5` |
| `SeqStep57Param8` | `0.5` |
| `SeqStep57Pitch` | `24` → +0 |
| `SeqStep57Type` | `0` |
| `SeqStep57Velo` | `0.8` |
| `SeqStep58Gate` | `1` |
| `SeqStep58Param1` | `0.5` |
| `SeqStep58Param2` | `0.5` |
| `SeqStep58Param3` | `0.5` |
| `SeqStep58Param4` | `0.5` |
| `SeqStep58Param5` | `0.5` |
| `SeqStep58Param6` | `0.5` |
| `SeqStep58Param7` | `0.5` |
| `SeqStep58Param8` | `0.5` |
| `SeqStep58Pitch` | `24` → +0 |
| `SeqStep58Type` | `0` |
| `SeqStep58Velo` | `0.8` |
| `SeqStep59Gate` | `1` |
| `SeqStep59Param1` | `0.5` |
| `SeqStep59Param2` | `0.5` |
| `SeqStep59Param3` | `0.5` |
| `SeqStep59Param4` | `0.5` |
| `SeqStep59Param5` | `0.5` |
| `SeqStep59Param6` | `0.5` |
| `SeqStep59Param7` | `0.5` |
| `SeqStep59Param8` | `0.5` |
| `SeqStep59Pitch` | `24` → +0 |
| `SeqStep59Type` | `0` |
| `SeqStep59Velo` | `0.8` |
| `SeqStep5Gate` | `0.5`; `1` |
| `SeqStep5Param1` | `0`; `0.5` |
| `SeqStep5Param2` | `0`; `0.5` |
| `SeqStep5Param3` | `0`; `0.5` |
| `SeqStep5Param4` | `0`; `0.5` |
| `SeqStep5Param5` | `0.5` |
| `SeqStep5Param6` | `0.5` |
| `SeqStep5Param7` | `0.5` |
| `SeqStep5Param8` | `0.5` |
| `SeqStep5Pitch` | `24` → +0 |
| `SeqStep5Type` | `0` |
| `SeqStep5Velo` | `0.8`; `1` |
| `SeqStep60Gate` | `1` |
| `SeqStep60Param1` | `0.5` |
| `SeqStep60Param2` | `0.5` |
| `SeqStep60Param3` | `0.5` |
| `SeqStep60Param4` | `0.5` |
| `SeqStep60Param5` | `0.5` |
| `SeqStep60Param6` | `0.5` |
| `SeqStep60Param7` | `0.5` |
| `SeqStep60Param8` | `0.5` |
| `SeqStep60Pitch` | `24` → +0 |
| `SeqStep60Type` | `0` |
| `SeqStep60Velo` | `0.8` |
| `SeqStep61Gate` | `1` |
| `SeqStep61Param1` | `0.5` |
| `SeqStep61Param2` | `0.5` |
| `SeqStep61Param3` | `0.5` |
| `SeqStep61Param4` | `0.5` |
| `SeqStep61Param5` | `0.5` |
| `SeqStep61Param6` | `0.5` |
| `SeqStep61Param7` | `0.5` |
| `SeqStep61Param8` | `0.5` |
| `SeqStep61Pitch` | `24` → +0 |
| `SeqStep61Type` | `0` |
| `SeqStep61Velo` | `0.8` |
| `SeqStep62Gate` | `1` |
| `SeqStep62Param1` | `0.5` |
| `SeqStep62Param2` | `0.5` |
| `SeqStep62Param3` | `0.5` |
| `SeqStep62Param4` | `0.5` |
| `SeqStep62Param5` | `0.5` |
| `SeqStep62Param6` | `0.5` |
| `SeqStep62Param7` | `0.5` |
| `SeqStep62Param8` | `0.5` |
| `SeqStep62Pitch` | `24` → +0 |
| `SeqStep62Type` | `0` |
| `SeqStep62Velo` | `0.8` |
| `SeqStep63Gate` | `1` |
| `SeqStep63Param1` | `0.5` |
| `SeqStep63Param2` | `0.5` |
| `SeqStep63Param3` | `0.5` |
| `SeqStep63Param4` | `0.5` |
| `SeqStep63Param5` | `0.5` |
| `SeqStep63Param6` | `0.5` |
| `SeqStep63Param7` | `0.5` |
| `SeqStep63Param8` | `0.5` |
| `SeqStep63Pitch` | `24` → +0 |
| `SeqStep63Type` | `0` |
| `SeqStep63Velo` | `0.8` |
| `SeqStep64Gate` | `1` |
| `SeqStep64Param1` | `0.5` |
| `SeqStep64Param2` | `0.5` |
| `SeqStep64Param3` | `0.5` |
| `SeqStep64Param4` | `0.5` |
| `SeqStep64Param5` | `0.5` |
| `SeqStep64Param6` | `0.5` |
| `SeqStep64Param7` | `0.5` |
| `SeqStep64Param8` | `0.5` |
| `SeqStep64Pitch` | `24` → +0 |
| `SeqStep64Type` | `0` |
| `SeqStep64Velo` | `0.8` |
| `SeqStep6Gate` | `0.5`; `1` |
| `SeqStep6Param1` | `0`; `0.5` |
| `SeqStep6Param2` | `0`; `0.5` |
| `SeqStep6Param3` | `0`; `0.5` |
| `SeqStep6Param4` | `0`; `0.5` |
| `SeqStep6Param5` | `0.5` |
| `SeqStep6Param6` | `0.5` |
| `SeqStep6Param7` | `0.5` |
| `SeqStep6Param8` | `0.5` |
| `SeqStep6Pitch` | `24` → +0 |
| `SeqStep6Type` | `0` |
| `SeqStep6Velo` | `0.8`; `1` |
| `SeqStep7Gate` | `0.5`; `1` |
| `SeqStep7Param1` | `0`; `0.5` |
| `SeqStep7Param2` | `0`; `0.5` |
| `SeqStep7Param3` | `0`; `0.5` |
| `SeqStep7Param4` | `0`; `0.5` |
| `SeqStep7Param5` | `0.5` |
| `SeqStep7Param6` | `0.5` |
| `SeqStep7Param7` | `0.5` |
| `SeqStep7Param8` | `0.5` |
| `SeqStep7Pitch` | `24` → +0 |
| `SeqStep7Type` | `0` |
| `SeqStep7Velo` | `0.8`; `1` |
| `SeqStep8Gate` | `0.5`; `1` |
| `SeqStep8Param1` | `0`; `0.5` |
| `SeqStep8Param2` | `0`; `0.5` |
| `SeqStep8Param3` | `0`; `0.5` |
| `SeqStep8Param4` | `0`; `0.5` |
| `SeqStep8Param5` | `0.5` |
| `SeqStep8Param6` | `0.5` |
| `SeqStep8Param7` | `0.5` |
| `SeqStep8Param8` | `0.5` |
| `SeqStep8Pitch` | `24` → +0 |
| `SeqStep8Type` | `0` |
| `SeqStep8Velo` | `0.8`; `1` |
| `SeqStep9Gate` | `0.5`; `1` |
| `SeqStep9Param1` | `0`; `0.5` |
| `SeqStep9Param2` | `0`; `0.5` |
| `SeqStep9Param3` | `0`; `0.5` |
| `SeqStep9Param4` | `0`; `0.5` |
| `SeqStep9Param5` | `0.5` |
| `SeqStep9Param6` | `0.5` |
| `SeqStep9Param7` | `0.5` |
| `SeqStep9Param8` | `0.5` |
| `SeqStep9Pitch` | `24` → +0 |
| `SeqStep9Type` | `0` |
| `SeqStep9Velo` | `0.8`; `1` |
| `TimbreMode` | `0` → Single |
| `TimeBpm` | `0.263158` |
| `TimeSync` | `0` → Internal; `1` → MIDI Clock |
| `TremoloDepth` | `0.75` |
| `TremoloPhaseDiff` | `0.5` |
| `TremoloShape` | `0` → Sine |
| `TremoloSmooth` | `0.5` |
| `TremoloSpeed` | `0.4` |
| `TremoloSync` | `0` → Off |
| `TremoloSyncPhase` | `0` |
| `TremoloSyncRatio` | `23` → 1/8 |
| `TuningDenom` | `0` |
| `TuningIntFromPrev` | `0` |
| `TuningIntFromRoot` | `0` |
| `TuningMidiPitch` | `0` |
| `TuningNum` | `0` |
| `TuningRepeatType` | `0` → Repeat |
| `TuningRootKey` | `0` → C-2 |
| `TuningStep` | `0` → 0 |
| `TuningStepType` | `0` → Interval |
| `UnisonoCount` | `0` → Off; `0.007874` → Off |
| `UnisonoDelay` | `0.25` |
| `UnisonoDetune` | `0`; `0.2` |
| `UnisonoPan` | `0.5` |
| `V4MacroDestSelection` | `0` → 1 |
| `V4MacroSelection` | `0` → Top-L |
| `V4Osc1Kernel1Active` | `1` → On |
| `V4Osc1Kernel1Attack` | `0` |
| `V4Osc1Kernel1Decay` | `0.1` |
| `V4Osc1Kernel1Decay2` | `0.1` |
| `V4Osc1Kernel1Detune` | `0.5` |
| `V4Osc1Kernel1Feedback` | `0` |
| `V4Osc1Kernel1HighBias` | `0.5` |
| `V4Osc1Kernel1HighSplit` | `72` → C4 |
| `V4Osc1Kernel1Level` | `0.25` |
| `V4Osc1Kernel1Level1` | `1` |
| `V4Osc1Kernel1LevelScale` | `1` → Quad |
| `V4Osc1Kernel1LowBias` | `0.5` |
| `V4Osc1Kernel1LowSplit` | `48` → C2 |
| `V4Osc1Kernel1ModSrc` | `0` → - |
| `V4Osc1Kernel1ModSrc2` | `0` → - |
| `V4Osc1Kernel1ModSrc3` | `0` → - |
| `V4Osc1Kernel1ModType` | `0` → Phase FM |
| `V4Osc1Kernel1OutDest` | `0` → [Out] |
| `V4Osc1Kernel1OutPan` | `0.5` |
| `V4Osc1Kernel1Phase` | `0` |
| `V4Osc1Kernel1PitchMode` | `0` → Ratio |
| `V4Osc1Kernel1Ratio` | `0` |
| `V4Osc1Kernel1Release` | `0.5` |
| `V4Osc1Kernel1Solo` | `0` → [Solo] |
| `V4Osc1Kernel1Sustain` | `1` |
| `V4Osc1Kernel1Type` | `0` → Sine |
| `V4Osc1Kernel1VeloDepth` | `0` |
| `V4Osc1Kernel1Wavetable` | `0` → Resonant  |
| `V4Osc1Kernel1WtbPos` | `0` |
| `V4Osc1Kernel2Active` | `1` → On |
| `V4Osc1Kernel2Attack` | `0` |
| `V4Osc1Kernel2Decay` | `0.1` |
| `V4Osc1Kernel2Decay2` | `0.1` |
| `V4Osc1Kernel2Detune` | `0.5` |
| `V4Osc1Kernel2Feedback` | `0` |
| `V4Osc1Kernel2HighBias` | `0.5` |
| `V4Osc1Kernel2HighSplit` | `72` → C4 |
| `V4Osc1Kernel2Level` | `0.5` |
| `V4Osc1Kernel2Level1` | `1` |
| `V4Osc1Kernel2LevelScale` | `1` → Quad |
| `V4Osc1Kernel2LowBias` | `0.5` |
| `V4Osc1Kernel2LowSplit` | `48` → C2 |
| `V4Osc1Kernel2ModSrc` | `1` → K1 |
| `V4Osc1Kernel2ModSrc2` | `0` → - |
| `V4Osc1Kernel2ModSrc3` | `0` → - |
| `V4Osc1Kernel2ModType` | `0` → Phase FM |
| `V4Osc1Kernel2OutDest` | `1` → Out |
| `V4Osc1Kernel2OutPan` | `0.5` |
| `V4Osc1Kernel2Phase` | `0` |
| `V4Osc1Kernel2PitchMode` | `0` → Ratio |
| `V4Osc1Kernel2Ratio` | `0` |
| `V4Osc1Kernel2Release` | `0.5` |
| `V4Osc1Kernel2Solo` | `0` → [Solo] |
| `V4Osc1Kernel2Sustain` | `1` |
| `V4Osc1Kernel2Type` | `0` → Sine |
| `V4Osc1Kernel2VeloDepth` | `0` |
| `V4Osc1Kernel2Wavetable` | `0` → Resonant  |
| `V4Osc1Kernel2WtbPos` | `0` |
| `V4Osc1Kernel3Active` | `0` → Off |
| `V4Osc1Kernel3Attack` | `0` |
| `V4Osc1Kernel3Decay` | `0.1` |
| `V4Osc1Kernel3Decay2` | `0.1` |
| `V4Osc1Kernel3Detune` | `0.5` |
| `V4Osc1Kernel3Feedback` | `0` |
| `V4Osc1Kernel3HighBias` | `0.5` |
| `V4Osc1Kernel3HighSplit` | `72` → C4 |
| `V4Osc1Kernel3Level` | `0.5` |
| `V4Osc1Kernel3Level1` | `1` |
| `V4Osc1Kernel3LevelScale` | `1` → Quad |
| `V4Osc1Kernel3LowBias` | `0.5` |
| `V4Osc1Kernel3LowSplit` | `48` → C2 |
| `V4Osc1Kernel3ModSrc` | `0` → - |
| `V4Osc1Kernel3ModSrc2` | `0` → - |
| `V4Osc1Kernel3ModSrc3` | `0` → - |
| `V4Osc1Kernel3ModType` | `0` → Phase FM |
| `V4Osc1Kernel3OutDest` | `0` → [Out] |
| `V4Osc1Kernel3OutPan` | `0.5` |
| `V4Osc1Kernel3Phase` | `0` |
| `V4Osc1Kernel3PitchMode` | `0` → Ratio |
| `V4Osc1Kernel3Ratio` | `0` |
| `V4Osc1Kernel3Release` | `0.5` |
| `V4Osc1Kernel3Solo` | `0` → [Solo] |
| `V4Osc1Kernel3Sustain` | `1` |
| `V4Osc1Kernel3Type` | `0` → Sine |
| `V4Osc1Kernel3VeloDepth` | `0` |
| `V4Osc1Kernel3Wavetable` | `0` → Resonant  |
| `V4Osc1Kernel3WtbPos` | `0` |
| `V4Osc1Kernel4Active` | `0` → Off |
| `V4Osc1Kernel4Attack` | `0` |
| `V4Osc1Kernel4Decay` | `0.1` |
| `V4Osc1Kernel4Decay2` | `0.1` |
| `V4Osc1Kernel4Detune` | `0.5` |
| `V4Osc1Kernel4Feedback` | `0` |
| `V4Osc1Kernel4HighBias` | `0.5` |
| `V4Osc1Kernel4HighSplit` | `72` → C4 |
| `V4Osc1Kernel4Level` | `0.5` |
| `V4Osc1Kernel4Level1` | `1` |
| `V4Osc1Kernel4LevelScale` | `1` → Quad |
| `V4Osc1Kernel4LowBias` | `0.5` |
| `V4Osc1Kernel4LowSplit` | `48` → C2 |
| `V4Osc1Kernel4ModSrc` | `0` → - |
| `V4Osc1Kernel4ModSrc2` | `0` → - |
| `V4Osc1Kernel4ModSrc3` | `0` → - |
| `V4Osc1Kernel4ModType` | `0` → Phase FM |
| `V4Osc1Kernel4OutDest` | `0` → [Out] |
| `V4Osc1Kernel4OutPan` | `0.5` |
| `V4Osc1Kernel4Phase` | `0` |
| `V4Osc1Kernel4PitchMode` | `0` → Ratio |
| `V4Osc1Kernel4Ratio` | `0` |
| `V4Osc1Kernel4Release` | `0.5` |
| `V4Osc1Kernel4Solo` | `0` → [Solo] |
| `V4Osc1Kernel4Sustain` | `1` |
| `V4Osc1Kernel4Type` | `0` → Sine |
| `V4Osc1Kernel4VeloDepth` | `0` |
| `V4Osc1Kernel4Wavetable` | `0` → Resonant  |
| `V4Osc1Kernel4WtbPos` | `0` |
| `V4Osc1Kernel5Active` | `0` → Off |
| `V4Osc1Kernel5Attack` | `0` |
| `V4Osc1Kernel5Decay` | `0.1` |
| `V4Osc1Kernel5Decay2` | `0.1` |
| `V4Osc1Kernel5Detune` | `0.5` |
| `V4Osc1Kernel5Feedback` | `0` |
| `V4Osc1Kernel5HighBias` | `0.5` |
| `V4Osc1Kernel5HighSplit` | `72` → C4 |
| `V4Osc1Kernel5Level` | `0.5` |
| `V4Osc1Kernel5Level1` | `1` |
| `V4Osc1Kernel5LevelScale` | `1` → Quad |
| `V4Osc1Kernel5LowBias` | `0.5` |
| `V4Osc1Kernel5LowSplit` | `48` → C2 |
| `V4Osc1Kernel5ModSrc` | `0` → - |
| `V4Osc1Kernel5ModSrc2` | `0` → - |
| `V4Osc1Kernel5ModSrc3` | `0` → - |
| `V4Osc1Kernel5ModType` | `0` → Phase FM |
| `V4Osc1Kernel5OutDest` | `0` → [Out] |
| `V4Osc1Kernel5OutPan` | `0.5` |
| `V4Osc1Kernel5Phase` | `0` |
| `V4Osc1Kernel5PitchMode` | `0` → Ratio |
| `V4Osc1Kernel5Ratio` | `0` |
| `V4Osc1Kernel5Release` | `0.5` |
| `V4Osc1Kernel5Solo` | `0` → [Solo] |
| `V4Osc1Kernel5Sustain` | `1` |
| `V4Osc1Kernel5Type` | `0` → Sine |
| `V4Osc1Kernel5VeloDepth` | `0` |
| `V4Osc1Kernel5Wavetable` | `0` → Resonant  |
| `V4Osc1Kernel5WtbPos` | `0` |
| `V4Osc1Kernel6Active` | `0` → Off |
| `V4Osc1Kernel6Attack` | `0` |
| `V4Osc1Kernel6Decay` | `0.1` |
| `V4Osc1Kernel6Decay2` | `0.1` |
| `V4Osc1Kernel6Detune` | `0.5` |
| `V4Osc1Kernel6Feedback` | `0` |
| `V4Osc1Kernel6HighBias` | `0.5` |
| `V4Osc1Kernel6HighSplit` | `72` → C4 |
| `V4Osc1Kernel6Level` | `0.5` |
| `V4Osc1Kernel6Level1` | `1` |
| `V4Osc1Kernel6LevelScale` | `1` → Quad |
| `V4Osc1Kernel6LowBias` | `0.5` |
| `V4Osc1Kernel6LowSplit` | `48` → C2 |
| `V4Osc1Kernel6ModSrc` | `0` → - |
| `V4Osc1Kernel6ModSrc2` | `0` → - |
| `V4Osc1Kernel6ModSrc3` | `0` → - |
| `V4Osc1Kernel6ModType` | `0` → Phase FM |
| `V4Osc1Kernel6OutDest` | `0` → [Out] |
| `V4Osc1Kernel6OutPan` | `0.5` |
| `V4Osc1Kernel6Phase` | `0` |
| `V4Osc1Kernel6PitchMode` | `0` → Ratio |
| `V4Osc1Kernel6Ratio` | `0` |
| `V4Osc1Kernel6Release` | `0.5` |
| `V4Osc1Kernel6Solo` | `0` → [Solo] |
| `V4Osc1Kernel6Sustain` | `1` |
| `V4Osc1Kernel6Type` | `0` → Sine |
| `V4Osc1Kernel6VeloDepth` | `0` |
| `V4Osc1Kernel6Wavetable` | `0` → Resonant  |
| `V4Osc1Kernel6WtbPos` | `0` |
| `V4Osc1Macro1` | `0` |
| `V4Osc1Macro1Amount1` | `0.5` |
| `V4Osc1Macro1Amount2` | `0.5` |
| `V4Osc1Macro1Amount3` | `0.5` |
| `V4Osc1Macro1Amount4` | `0.5` |
| `V4Osc1Macro1Amount5` | `0.5` |
| `V4Osc1Macro1Amount6` | `0.5` |
| `V4Osc1Macro1Dest1` | `0` → Off |
| `V4Osc1Macro1Dest2` | `0` → Off |
| `V4Osc1Macro1Dest3` | `0` → Off |
| `V4Osc1Macro1Dest4` | `0` → Off |
| `V4Osc1Macro1Dest5` | `0` → Off |
| `V4Osc1Macro1Dest6` | `0` → Off |
| `V4Osc1Macro1Name` | `0` → Top-L |
| `V4Osc1Macro2` | `0` |
| `V4Osc1Macro2Amount1` | `0.5` |
| `V4Osc1Macro2Amount2` | `0.5` |
| `V4Osc1Macro2Amount3` | `0.5` |
| `V4Osc1Macro2Amount4` | `0.5` |
| `V4Osc1Macro2Amount5` | `0.5` |
| `V4Osc1Macro2Amount6` | `0.5` |
| `V4Osc1Macro2Dest1` | `0` → Off |
| `V4Osc1Macro2Dest2` | `0` → Off |
| `V4Osc1Macro2Dest3` | `0` → Off |
| `V4Osc1Macro2Dest4` | `0` → Off |
| `V4Osc1Macro2Dest5` | `0` → Off |
| `V4Osc1Macro2Dest6` | `0` → Off |
| `V4Osc1Macro2Name` | `0` → Top-R |
| `V4Osc1Macro3` | `0` |
| `V4Osc1Macro3Amount1` | `0.5` |
| `V4Osc1Macro3Amount2` | `0.5` |
| `V4Osc1Macro3Amount3` | `0.5` |
| `V4Osc1Macro3Amount4` | `0.5` |
| `V4Osc1Macro3Amount5` | `0.5` |
| `V4Osc1Macro3Amount6` | `0.5` |
| `V4Osc1Macro3Dest1` | `0` → Off |
| `V4Osc1Macro3Dest2` | `0` → Off |
| `V4Osc1Macro3Dest3` | `0` → Off |
| `V4Osc1Macro3Dest4` | `0` → Off |
| `V4Osc1Macro3Dest5` | `0` → Off |
| `V4Osc1Macro3Dest6` | `0` → Off |
| `V4Osc1Macro3Name` | `0` → Center |
| `V4Osc1Macro4` | `0` |
| `V4Osc1Macro4Amount1` | `0.5` |
| `V4Osc1Macro4Amount2` | `0.5` |
| `V4Osc1Macro4Amount3` | `0.5` |
| `V4Osc1Macro4Amount4` | `0.5` |
| `V4Osc1Macro4Amount5` | `0.5` |
| `V4Osc1Macro4Amount6` | `0.5` |
| `V4Osc1Macro4Dest1` | `0` → Off |
| `V4Osc1Macro4Dest2` | `0` → Off |
| `V4Osc1Macro4Dest3` | `0` → Off |
| `V4Osc1Macro4Dest4` | `0` → Off |
| `V4Osc1Macro4Dest5` | `0` → Off |
| `V4Osc1Macro4Dest6` | `0` → Off |
| `V4Osc1Macro4Name` | `0` → Bottom-L; `0.25` → Bottom-L |
| `V4Osc1Macro5` | `0` |
| `V4Osc1Macro5Amount1` | `0.5` |
| `V4Osc1Macro5Amount2` | `0.5` |
| `V4Osc1Macro5Amount3` | `0.5` |
| `V4Osc1Macro5Amount4` | `0.5` |
| `V4Osc1Macro5Amount5` | `0.5` |
| `V4Osc1Macro5Amount6` | `0.5` |
| `V4Osc1Macro5Dest1` | `0` → Off |
| `V4Osc1Macro5Dest2` | `0` → Off |
| `V4Osc1Macro5Dest3` | `0` → Off |
| `V4Osc1Macro5Dest4` | `0` → Off |
| `V4Osc1Macro5Dest5` | `0` → Off |
| `V4Osc1Macro5Dest6` | `0` → Off |
| `V4Osc1Macro5Name` | `0` → Bottom-R |
| `V4Osc1TemplateName` | `0.25` → Custom; `0.75` → Custom |
| `V4Osc2Kernel1Active` | `1` → On |
| `V4Osc2Kernel1Attack` | `0` |
| `V4Osc2Kernel1Decay` | `0.1` |
| `V4Osc2Kernel1Decay2` | `0.1` |
| `V4Osc2Kernel1Detune` | `0.5` |
| `V4Osc2Kernel1Feedback` | `0` |
| `V4Osc2Kernel1HighBias` | `0.5` |
| `V4Osc2Kernel1HighSplit` | `72` → C4 |
| `V4Osc2Kernel1Level` | `0.25` |
| `V4Osc2Kernel1Level1` | `1` |
| `V4Osc2Kernel1LevelScale` | `1` → Quad |
| `V4Osc2Kernel1LowBias` | `0.5` |
| `V4Osc2Kernel1LowSplit` | `48` → C2 |
| `V4Osc2Kernel1ModSrc` | `0` → - |
| `V4Osc2Kernel1ModSrc2` | `0` → - |
| `V4Osc2Kernel1ModSrc3` | `0` → - |
| `V4Osc2Kernel1ModType` | `0` → Phase FM |
| `V4Osc2Kernel1OutDest` | `0` → [Out] |
| `V4Osc2Kernel1OutPan` | `0.5` |
| `V4Osc2Kernel1Phase` | `0` |
| `V4Osc2Kernel1PitchMode` | `0` → Ratio |
| `V4Osc2Kernel1Ratio` | `0` |
| `V4Osc2Kernel1Release` | `0.5` |
| `V4Osc2Kernel1Solo` | `0` → [Solo] |
| `V4Osc2Kernel1Sustain` | `1` |
| `V4Osc2Kernel1Type` | `0` → Sine |
| `V4Osc2Kernel1VeloDepth` | `0` |
| `V4Osc2Kernel1Wavetable` | `0` → Resonant  |
| `V4Osc2Kernel1WtbPos` | `0` |
| `V4Osc2Kernel2Active` | `1` → On |
| `V4Osc2Kernel2Attack` | `0` |
| `V4Osc2Kernel2Decay` | `0.1` |
| `V4Osc2Kernel2Decay2` | `0.1` |
| `V4Osc2Kernel2Detune` | `0.5` |
| `V4Osc2Kernel2Feedback` | `0` |
| `V4Osc2Kernel2HighBias` | `0.5` |
| `V4Osc2Kernel2HighSplit` | `72` → C4 |
| `V4Osc2Kernel2Level` | `0.5` |
| `V4Osc2Kernel2Level1` | `1` |
| `V4Osc2Kernel2LevelScale` | `1` → Quad |
| `V4Osc2Kernel2LowBias` | `0.5` |
| `V4Osc2Kernel2LowSplit` | `48` → C2 |
| `V4Osc2Kernel2ModSrc` | `1` → K1 |
| `V4Osc2Kernel2ModSrc2` | `0` → - |
| `V4Osc2Kernel2ModSrc3` | `0` → - |
| `V4Osc2Kernel2ModType` | `0` → Phase FM |
| `V4Osc2Kernel2OutDest` | `1` → Out |
| `V4Osc2Kernel2OutPan` | `0.5` |
| `V4Osc2Kernel2Phase` | `0` |
| `V4Osc2Kernel2PitchMode` | `0` → Ratio |
| `V4Osc2Kernel2Ratio` | `0` |
| `V4Osc2Kernel2Release` | `0.5` |
| `V4Osc2Kernel2Solo` | `0` → [Solo] |
| `V4Osc2Kernel2Sustain` | `1` |
| `V4Osc2Kernel2Type` | `0` → Sine |
| `V4Osc2Kernel2VeloDepth` | `0` |
| `V4Osc2Kernel2Wavetable` | `0` → Resonant  |
| `V4Osc2Kernel2WtbPos` | `0` |
| `V4Osc2Kernel3Active` | `0` → Off |
| `V4Osc2Kernel3Attack` | `0` |
| `V4Osc2Kernel3Decay` | `0.1` |
| `V4Osc2Kernel3Decay2` | `0.1` |
| `V4Osc2Kernel3Detune` | `0.5` |
| `V4Osc2Kernel3Feedback` | `0` |
| `V4Osc2Kernel3HighBias` | `0.5` |
| `V4Osc2Kernel3HighSplit` | `72` → C4 |
| `V4Osc2Kernel3Level` | `0.5` |
| `V4Osc2Kernel3Level1` | `1` |
| `V4Osc2Kernel3LevelScale` | `1` → Quad |
| `V4Osc2Kernel3LowBias` | `0.5` |
| `V4Osc2Kernel3LowSplit` | `48` → C2 |
| `V4Osc2Kernel3ModSrc` | `0` → - |
| `V4Osc2Kernel3ModSrc2` | `0` → - |
| `V4Osc2Kernel3ModSrc3` | `0` → - |
| `V4Osc2Kernel3ModType` | `0` → Phase FM |
| `V4Osc2Kernel3OutDest` | `0` → [Out] |
| `V4Osc2Kernel3OutPan` | `0.5` |
| `V4Osc2Kernel3Phase` | `0` |
| `V4Osc2Kernel3PitchMode` | `0` → Ratio |
| `V4Osc2Kernel3Ratio` | `0` |
| `V4Osc2Kernel3Release` | `0.5` |
| `V4Osc2Kernel3Solo` | `0` → [Solo] |
| `V4Osc2Kernel3Sustain` | `1` |
| `V4Osc2Kernel3Type` | `0` → Sine |
| `V4Osc2Kernel3VeloDepth` | `0` |
| `V4Osc2Kernel3Wavetable` | `0` → Resonant  |
| `V4Osc2Kernel3WtbPos` | `0` |
| `V4Osc2Kernel4Active` | `0` → Off |
| `V4Osc2Kernel4Attack` | `0` |
| `V4Osc2Kernel4Decay` | `0.1` |
| `V4Osc2Kernel4Decay2` | `0.1` |
| `V4Osc2Kernel4Detune` | `0.5` |
| `V4Osc2Kernel4Feedback` | `0` |
| `V4Osc2Kernel4HighBias` | `0.5` |
| `V4Osc2Kernel4HighSplit` | `72` → C4 |
| `V4Osc2Kernel4Level` | `0.5` |
| `V4Osc2Kernel4Level1` | `1` |
| `V4Osc2Kernel4LevelScale` | `1` → Quad |
| `V4Osc2Kernel4LowBias` | `0.5` |
| `V4Osc2Kernel4LowSplit` | `48` → C2 |
| `V4Osc2Kernel4ModSrc` | `0` → - |
| `V4Osc2Kernel4ModSrc2` | `0` → - |
| `V4Osc2Kernel4ModSrc3` | `0` → - |
| `V4Osc2Kernel4ModType` | `0` → Phase FM |
| `V4Osc2Kernel4OutDest` | `0` → [Out] |
| `V4Osc2Kernel4OutPan` | `0.5` |
| `V4Osc2Kernel4Phase` | `0` |
| `V4Osc2Kernel4PitchMode` | `0` → Ratio |
| `V4Osc2Kernel4Ratio` | `0` |
| `V4Osc2Kernel4Release` | `0.5` |
| `V4Osc2Kernel4Solo` | `0` → [Solo] |
| `V4Osc2Kernel4Sustain` | `1` |
| `V4Osc2Kernel4Type` | `0` → Sine |
| `V4Osc2Kernel4VeloDepth` | `0` |
| `V4Osc2Kernel4Wavetable` | `0` → Resonant  |
| `V4Osc2Kernel4WtbPos` | `0` |
| `V4Osc2Kernel5Active` | `0` → Off |
| `V4Osc2Kernel5Attack` | `0` |
| `V4Osc2Kernel5Decay` | `0.1` |
| `V4Osc2Kernel5Decay2` | `0.1` |
| `V4Osc2Kernel5Detune` | `0.5` |
| `V4Osc2Kernel5Feedback` | `0` |
| `V4Osc2Kernel5HighBias` | `0.5` |
| `V4Osc2Kernel5HighSplit` | `72` → C4 |
| `V4Osc2Kernel5Level` | `0.5` |
| `V4Osc2Kernel5Level1` | `1` |
| `V4Osc2Kernel5LevelScale` | `1` → Quad |
| `V4Osc2Kernel5LowBias` | `0.5` |
| `V4Osc2Kernel5LowSplit` | `48` → C2 |
| `V4Osc2Kernel5ModSrc` | `0` → - |
| `V4Osc2Kernel5ModSrc2` | `0` → - |
| `V4Osc2Kernel5ModSrc3` | `0` → - |
| `V4Osc2Kernel5ModType` | `0` → Phase FM |
| `V4Osc2Kernel5OutDest` | `0` → [Out] |
| `V4Osc2Kernel5OutPan` | `0.5` |
| `V4Osc2Kernel5Phase` | `0` |
| `V4Osc2Kernel5PitchMode` | `0` → Ratio |
| `V4Osc2Kernel5Ratio` | `0` |
| `V4Osc2Kernel5Release` | `0.5` |
| `V4Osc2Kernel5Solo` | `0` → [Solo] |
| `V4Osc2Kernel5Sustain` | `1` |
| `V4Osc2Kernel5Type` | `0` → Sine |
| `V4Osc2Kernel5VeloDepth` | `0` |
| `V4Osc2Kernel5Wavetable` | `0` → Resonant  |
| `V4Osc2Kernel5WtbPos` | `0` |
| `V4Osc2Kernel6Active` | `0` → Off |
| `V4Osc2Kernel6Attack` | `0` |
| `V4Osc2Kernel6Decay` | `0.1` |
| `V4Osc2Kernel6Decay2` | `0.1` |
| `V4Osc2Kernel6Detune` | `0.5` |
| `V4Osc2Kernel6Feedback` | `0` |
| `V4Osc2Kernel6HighBias` | `0.5` |
| `V4Osc2Kernel6HighSplit` | `72` → C4 |
| `V4Osc2Kernel6Level` | `0.5` |
| `V4Osc2Kernel6Level1` | `1` |
| `V4Osc2Kernel6LevelScale` | `1` → Quad |
| `V4Osc2Kernel6LowBias` | `0.5` |
| `V4Osc2Kernel6LowSplit` | `48` → C2 |
| `V4Osc2Kernel6ModSrc` | `0` → - |
| `V4Osc2Kernel6ModSrc2` | `0` → - |
| `V4Osc2Kernel6ModSrc3` | `0` → - |
| `V4Osc2Kernel6ModType` | `0` → Phase FM |
| `V4Osc2Kernel6OutDest` | `0` → [Out] |
| `V4Osc2Kernel6OutPan` | `0.5` |
| `V4Osc2Kernel6Phase` | `0` |
| `V4Osc2Kernel6PitchMode` | `0` → Ratio |
| `V4Osc2Kernel6Ratio` | `0` |
| `V4Osc2Kernel6Release` | `0.5` |
| `V4Osc2Kernel6Solo` | `0` → [Solo] |
| `V4Osc2Kernel6Sustain` | `1` |
| `V4Osc2Kernel6Type` | `0` → Sine |
| `V4Osc2Kernel6VeloDepth` | `0` |
| `V4Osc2Kernel6Wavetable` | `0` → Resonant  |
| `V4Osc2Kernel6WtbPos` | `0` |
| `V4Osc2Macro1` | `0` |
| `V4Osc2Macro1Amount1` | `0.5` |
| `V4Osc2Macro1Amount2` | `0.5` |
| `V4Osc2Macro1Amount3` | `0.5` |
| `V4Osc2Macro1Amount4` | `0.5` |
| `V4Osc2Macro1Amount5` | `0.5` |
| `V4Osc2Macro1Amount6` | `0.5` |
| `V4Osc2Macro1Dest1` | `0` → Off |
| `V4Osc2Macro1Dest2` | `0` → Off |
| `V4Osc2Macro1Dest3` | `0` → Off |
| `V4Osc2Macro1Dest4` | `0` → Off |
| `V4Osc2Macro1Dest5` | `0` → Off |
| `V4Osc2Macro1Dest6` | `0` → Off |
| `V4Osc2Macro1Name` | `0` → Top-L; `0.5` → Top-L |
| `V4Osc2Macro2` | `0` |
| `V4Osc2Macro2Amount1` | `0.5` |
| `V4Osc2Macro2Amount2` | `0.5` |
| `V4Osc2Macro2Amount3` | `0.5` |
| `V4Osc2Macro2Amount4` | `0.5` |
| `V4Osc2Macro2Amount5` | `0.5` |
| `V4Osc2Macro2Amount6` | `0.5` |
| `V4Osc2Macro2Dest1` | `0` → Off |
| `V4Osc2Macro2Dest2` | `0` → Off |
| `V4Osc2Macro2Dest3` | `0` → Off |
| `V4Osc2Macro2Dest4` | `0` → Off |
| `V4Osc2Macro2Dest5` | `0` → Off |
| `V4Osc2Macro2Dest6` | `0` → Off |
| `V4Osc2Macro2Name` | `0` → Top-R; `0.5` → Top-R; `1` → Top-R |
| `V4Osc2Macro3` | `0` |
| `V4Osc2Macro3Amount1` | `0.5` |
| `V4Osc2Macro3Amount2` | `0.5` |
| `V4Osc2Macro3Amount3` | `0.5` |
| `V4Osc2Macro3Amount4` | `0.5` |
| `V4Osc2Macro3Amount5` | `0.5` |
| `V4Osc2Macro3Amount6` | `0.5` |
| `V4Osc2Macro3Dest1` | `0` → Off |
| `V4Osc2Macro3Dest2` | `0` → Off |
| `V4Osc2Macro3Dest3` | `0` → Off |
| `V4Osc2Macro3Dest4` | `0` → Off |
| `V4Osc2Macro3Dest5` | `0` → Off |
| `V4Osc2Macro3Dest6` | `0` → Off |
| `V4Osc2Macro3Name` | `0` → Center; `0.5` → Center |
| `V4Osc2Macro4` | `0` |
| `V4Osc2Macro4Amount1` | `0.5` |
| `V4Osc2Macro4Amount2` | `0.5` |
| `V4Osc2Macro4Amount3` | `0.5` |
| `V4Osc2Macro4Amount4` | `0.5` |
| `V4Osc2Macro4Amount5` | `0.5` |
| `V4Osc2Macro4Amount6` | `0.5` |
| `V4Osc2Macro4Dest1` | `0` → Off |
| `V4Osc2Macro4Dest2` | `0` → Off |
| `V4Osc2Macro4Dest3` | `0` → Off |
| `V4Osc2Macro4Dest4` | `0` → Off |
| `V4Osc2Macro4Dest5` | `0` → Off |
| `V4Osc2Macro4Dest6` | `0` → Off |
| `V4Osc2Macro4Name` | `0` → Bottom-L; `0.24` → Bottom-L; `0.5` → Bottom-L |
| `V4Osc2Macro5` | `0` |
| `V4Osc2Macro5Amount1` | `0.5` |
| `V4Osc2Macro5Amount2` | `0.5` |
| `V4Osc2Macro5Amount3` | `0.5` |
| `V4Osc2Macro5Amount4` | `0.5` |
| `V4Osc2Macro5Amount5` | `0.5` |
| `V4Osc2Macro5Amount6` | `0.5` |
| `V4Osc2Macro5Dest1` | `0` → Off |
| `V4Osc2Macro5Dest2` | `0` → Off |
| `V4Osc2Macro5Dest3` | `0` → Off |
| `V4Osc2Macro5Dest4` | `0` → Off |
| `V4Osc2Macro5Dest5` | `0` → Off |
| `V4Osc2Macro5Dest6` | `0` → Off |
| `V4Osc2Macro5Name` | `0` → Bottom-R; `1` → Bottom-R |
| `V4Osc2TemplateName` | `0` → Custom; `0.5` → Custom; `1` → Custom |
| `V4Osc3Kernel1Active` | `1` → On |
| `V4Osc3Kernel1Attack` | `0` |
| `V4Osc3Kernel1Decay` | `0.1` |
| `V4Osc3Kernel1Decay2` | `0.1` |
| `V4Osc3Kernel1Detune` | `0.5` |
| `V4Osc3Kernel1Feedback` | `0` |
| `V4Osc3Kernel1HighBias` | `0.5` |
| `V4Osc3Kernel1HighSplit` | `72` → C4 |
| `V4Osc3Kernel1Level` | `0.25` |
| `V4Osc3Kernel1Level1` | `1` |
| `V4Osc3Kernel1LevelScale` | `1` → Quad |
| `V4Osc3Kernel1LowBias` | `0.5` |
| `V4Osc3Kernel1LowSplit` | `48` → C2 |
| `V4Osc3Kernel1ModSrc` | `0` → - |
| `V4Osc3Kernel1ModSrc2` | `0` → - |
| `V4Osc3Kernel1ModSrc3` | `0` → - |
| `V4Osc3Kernel1ModType` | `0` → Phase FM |
| `V4Osc3Kernel1OutDest` | `0` → [Out] |
| `V4Osc3Kernel1OutPan` | `0.5` |
| `V4Osc3Kernel1Phase` | `0` |
| `V4Osc3Kernel1PitchMode` | `0` → Ratio |
| `V4Osc3Kernel1Ratio` | `0` |
| `V4Osc3Kernel1Release` | `0.5` |
| `V4Osc3Kernel1Solo` | `0` → [Solo] |
| `V4Osc3Kernel1Sustain` | `1` |
| `V4Osc3Kernel1Type` | `0` → Sine |
| `V4Osc3Kernel1VeloDepth` | `0` |
| `V4Osc3Kernel1Wavetable` | `0` → Resonant  |
| `V4Osc3Kernel1WtbPos` | `0` |
| `V4Osc3Kernel2Active` | `1` → On |
| `V4Osc3Kernel2Attack` | `0` |
| `V4Osc3Kernel2Decay` | `0.1` |
| `V4Osc3Kernel2Decay2` | `0.1` |
| `V4Osc3Kernel2Detune` | `0.5` |
| `V4Osc3Kernel2Feedback` | `0` |
| `V4Osc3Kernel2HighBias` | `0.5` |
| `V4Osc3Kernel2HighSplit` | `72` → C4 |
| `V4Osc3Kernel2Level` | `0.5` |
| `V4Osc3Kernel2Level1` | `1` |
| `V4Osc3Kernel2LevelScale` | `1` → Quad |
| `V4Osc3Kernel2LowBias` | `0.5` |
| `V4Osc3Kernel2LowSplit` | `48` → C2 |
| `V4Osc3Kernel2ModSrc` | `1` → K1 |
| `V4Osc3Kernel2ModSrc2` | `0` → - |
| `V4Osc3Kernel2ModSrc3` | `0` → - |
| `V4Osc3Kernel2ModType` | `0` → Phase FM |
| `V4Osc3Kernel2OutDest` | `1` → Out |
| `V4Osc3Kernel2OutPan` | `0.5` |
| `V4Osc3Kernel2Phase` | `0` |
| `V4Osc3Kernel2PitchMode` | `0` → Ratio |
| `V4Osc3Kernel2Ratio` | `0` |
| `V4Osc3Kernel2Release` | `0.5` |
| `V4Osc3Kernel2Solo` | `0` → [Solo] |
| `V4Osc3Kernel2Sustain` | `1` |
| `V4Osc3Kernel2Type` | `0` → Sine |
| `V4Osc3Kernel2VeloDepth` | `0` |
| `V4Osc3Kernel2Wavetable` | `0` → Resonant  |
| `V4Osc3Kernel2WtbPos` | `0` |
| `V4Osc3Kernel3Active` | `0` → Off |
| `V4Osc3Kernel3Attack` | `0` |
| `V4Osc3Kernel3Decay` | `0.1` |
| `V4Osc3Kernel3Decay2` | `0.1` |
| `V4Osc3Kernel3Detune` | `0.5` |
| `V4Osc3Kernel3Feedback` | `0` |
| `V4Osc3Kernel3HighBias` | `0.5` |
| `V4Osc3Kernel3HighSplit` | `72` → C4 |
| `V4Osc3Kernel3Level` | `0.5` |
| `V4Osc3Kernel3Level1` | `1` |
| `V4Osc3Kernel3LevelScale` | `1` → Quad |
| `V4Osc3Kernel3LowBias` | `0.5` |
| `V4Osc3Kernel3LowSplit` | `48` → C2 |
| `V4Osc3Kernel3ModSrc` | `0` → - |
| `V4Osc3Kernel3ModSrc2` | `0` → - |
| `V4Osc3Kernel3ModSrc3` | `0` → - |
| `V4Osc3Kernel3ModType` | `0` → Phase FM |
| `V4Osc3Kernel3OutDest` | `0` → [Out] |
| `V4Osc3Kernel3OutPan` | `0.5` |
| `V4Osc3Kernel3Phase` | `0` |
| `V4Osc3Kernel3PitchMode` | `0` → Ratio |
| `V4Osc3Kernel3Ratio` | `0` |
| `V4Osc3Kernel3Release` | `0.5` |
| `V4Osc3Kernel3Solo` | `0` → [Solo] |
| `V4Osc3Kernel3Sustain` | `1` |
| `V4Osc3Kernel3Type` | `0` → Sine |
| `V4Osc3Kernel3VeloDepth` | `0` |
| `V4Osc3Kernel3Wavetable` | `0` → Resonant  |
| `V4Osc3Kernel3WtbPos` | `0` |
| `V4Osc3Kernel4Active` | `0` → Off |
| `V4Osc3Kernel4Attack` | `0` |
| `V4Osc3Kernel4Decay` | `0.1` |
| `V4Osc3Kernel4Decay2` | `0.1` |
| `V4Osc3Kernel4Detune` | `0.5` |
| `V4Osc3Kernel4Feedback` | `0` |
| `V4Osc3Kernel4HighBias` | `0.5` |
| `V4Osc3Kernel4HighSplit` | `72` → C4 |
| `V4Osc3Kernel4Level` | `0.5` |
| `V4Osc3Kernel4Level1` | `1` |
| `V4Osc3Kernel4LevelScale` | `1` → Quad |
| `V4Osc3Kernel4LowBias` | `0.5` |
| `V4Osc3Kernel4LowSplit` | `48` → C2 |
| `V4Osc3Kernel4ModSrc` | `0` → - |
| `V4Osc3Kernel4ModSrc2` | `0` → - |
| `V4Osc3Kernel4ModSrc3` | `0` → - |
| `V4Osc3Kernel4ModType` | `0` → Phase FM |
| `V4Osc3Kernel4OutDest` | `0` → [Out] |
| `V4Osc3Kernel4OutPan` | `0.5` |
| `V4Osc3Kernel4Phase` | `0` |
| `V4Osc3Kernel4PitchMode` | `0` → Ratio |
| `V4Osc3Kernel4Ratio` | `0` |
| `V4Osc3Kernel4Release` | `0.5` |
| `V4Osc3Kernel4Solo` | `0` → [Solo] |
| `V4Osc3Kernel4Sustain` | `1` |
| `V4Osc3Kernel4Type` | `0` → Sine |
| `V4Osc3Kernel4VeloDepth` | `0` |
| `V4Osc3Kernel4Wavetable` | `0` → Resonant  |
| `V4Osc3Kernel4WtbPos` | `0` |
| `V4Osc3Kernel5Active` | `0` → Off |
| `V4Osc3Kernel5Attack` | `0` |
| `V4Osc3Kernel5Decay` | `0.1` |
| `V4Osc3Kernel5Decay2` | `0.1` |
| `V4Osc3Kernel5Detune` | `0.5` |
| `V4Osc3Kernel5Feedback` | `0` |
| `V4Osc3Kernel5HighBias` | `0.5` |
| `V4Osc3Kernel5HighSplit` | `72` → C4 |
| `V4Osc3Kernel5Level` | `0.5` |
| `V4Osc3Kernel5Level1` | `1` |
| `V4Osc3Kernel5LevelScale` | `1` → Quad |
| `V4Osc3Kernel5LowBias` | `0.5` |
| `V4Osc3Kernel5LowSplit` | `48` → C2 |
| `V4Osc3Kernel5ModSrc` | `0` → - |
| `V4Osc3Kernel5ModSrc2` | `0` → - |
| `V4Osc3Kernel5ModSrc3` | `0` → - |
| `V4Osc3Kernel5ModType` | `0` → Phase FM |
| `V4Osc3Kernel5OutDest` | `0` → [Out] |
| `V4Osc3Kernel5OutPan` | `0.5` |
| `V4Osc3Kernel5Phase` | `0` |
| `V4Osc3Kernel5PitchMode` | `0` → Ratio |
| `V4Osc3Kernel5Ratio` | `0` |
| `V4Osc3Kernel5Release` | `0.5` |
| `V4Osc3Kernel5Solo` | `0` → [Solo] |
| `V4Osc3Kernel5Sustain` | `1` |
| `V4Osc3Kernel5Type` | `0` → Sine |
| `V4Osc3Kernel5VeloDepth` | `0` |
| `V4Osc3Kernel5Wavetable` | `0` → Resonant  |
| `V4Osc3Kernel5WtbPos` | `0` |
| `V4Osc3Kernel6Active` | `0` → Off |
| `V4Osc3Kernel6Attack` | `0` |
| `V4Osc3Kernel6Decay` | `0.1` |
| `V4Osc3Kernel6Decay2` | `0.1` |
| `V4Osc3Kernel6Detune` | `0.5` |
| `V4Osc3Kernel6Feedback` | `0` |
| `V4Osc3Kernel6HighBias` | `0.5` |
| `V4Osc3Kernel6HighSplit` | `72` → C4 |
| `V4Osc3Kernel6Level` | `0.5` |
| `V4Osc3Kernel6Level1` | `1` |
| `V4Osc3Kernel6LevelScale` | `1` → Quad |
| `V4Osc3Kernel6LowBias` | `0.5` |
| `V4Osc3Kernel6LowSplit` | `48` → C2 |
| `V4Osc3Kernel6ModSrc` | `0` → - |
| `V4Osc3Kernel6ModSrc2` | `0` → - |
| `V4Osc3Kernel6ModSrc3` | `0` → - |
| `V4Osc3Kernel6ModType` | `0` → Phase FM |
| `V4Osc3Kernel6OutDest` | `0` → [Out] |
| `V4Osc3Kernel6OutPan` | `0.5` |
| `V4Osc3Kernel6Phase` | `0` |
| `V4Osc3Kernel6PitchMode` | `0` → Ratio |
| `V4Osc3Kernel6Ratio` | `0` |
| `V4Osc3Kernel6Release` | `0.5` |
| `V4Osc3Kernel6Solo` | `0` → [Solo] |
| `V4Osc3Kernel6Sustain` | `1` |
| `V4Osc3Kernel6Type` | `0` → Sine |
| `V4Osc3Kernel6VeloDepth` | `0` |
| `V4Osc3Kernel6Wavetable` | `0` → Resonant  |
| `V4Osc3Kernel6WtbPos` | `0` |
| `V4Osc3Macro1` | `0` |
| `V4Osc3Macro1Amount1` | `0.5` |
| `V4Osc3Macro1Amount2` | `0.5` |
| `V4Osc3Macro1Amount3` | `0.5` |
| `V4Osc3Macro1Amount4` | `0.5` |
| `V4Osc3Macro1Amount5` | `0.5` |
| `V4Osc3Macro1Amount6` | `0.5` |
| `V4Osc3Macro1Dest1` | `0` → Off |
| `V4Osc3Macro1Dest2` | `0` → Off |
| `V4Osc3Macro1Dest3` | `0` → Off |
| `V4Osc3Macro1Dest4` | `0` → Off |
| `V4Osc3Macro1Dest5` | `0` → Off |
| `V4Osc3Macro1Dest6` | `0` → Off |
| `V4Osc3Macro1Name` | `0` → Top-L; `0.5` → Top-L |
| `V4Osc3Macro2` | `0` |
| `V4Osc3Macro2Amount1` | `0.5` |
| `V4Osc3Macro2Amount2` | `0.5` |
| `V4Osc3Macro2Amount3` | `0.5` |
| `V4Osc3Macro2Amount4` | `0.5` |
| `V4Osc3Macro2Amount5` | `0.5` |
| `V4Osc3Macro2Amount6` | `0.5` |
| `V4Osc3Macro2Dest1` | `0` → Off |
| `V4Osc3Macro2Dest2` | `0` → Off |
| `V4Osc3Macro2Dest3` | `0` → Off |
| `V4Osc3Macro2Dest4` | `0` → Off |
| `V4Osc3Macro2Dest5` | `0` → Off |
| `V4Osc3Macro2Dest6` | `0` → Off |
| `V4Osc3Macro2Name` | `0` → Top-R; `0.5` → Top-R; `1` → Top-R |
| `V4Osc3Macro3` | `0` |
| `V4Osc3Macro3Amount1` | `0.5` |
| `V4Osc3Macro3Amount2` | `0.5` |
| `V4Osc3Macro3Amount3` | `0.5` |
| `V4Osc3Macro3Amount4` | `0.5` |
| `V4Osc3Macro3Amount5` | `0.5` |
| `V4Osc3Macro3Amount6` | `0.5` |
| `V4Osc3Macro3Dest1` | `0` → Off |
| `V4Osc3Macro3Dest2` | `0` → Off |
| `V4Osc3Macro3Dest3` | `0` → Off |
| `V4Osc3Macro3Dest4` | `0` → Off |
| `V4Osc3Macro3Dest5` | `0` → Off |
| `V4Osc3Macro3Dest6` | `0` → Off |
| `V4Osc3Macro3Name` | `0` → Center |
| `V4Osc3Macro4` | `0` |
| `V4Osc3Macro4Amount1` | `0.5` |
| `V4Osc3Macro4Amount2` | `0.5` |
| `V4Osc3Macro4Amount3` | `0.5` |
| `V4Osc3Macro4Amount4` | `0.5` |
| `V4Osc3Macro4Amount5` | `0.5` |
| `V4Osc3Macro4Amount6` | `0.5` |
| `V4Osc3Macro4Dest1` | `0` → Off |
| `V4Osc3Macro4Dest2` | `0` → Off |
| `V4Osc3Macro4Dest3` | `0` → Off |
| `V4Osc3Macro4Dest4` | `0` → Off |
| `V4Osc3Macro4Dest5` | `0` → Off |
| `V4Osc3Macro4Dest6` | `0` → Off |
| `V4Osc3Macro4Name` | `0` → Bottom-L; `0.5` → Bottom-L |
| `V4Osc3Macro5` | `0` |
| `V4Osc3Macro5Amount1` | `0.5` |
| `V4Osc3Macro5Amount2` | `0.5` |
| `V4Osc3Macro5Amount3` | `0.5` |
| `V4Osc3Macro5Amount4` | `0.5` |
| `V4Osc3Macro5Amount5` | `0.5` |
| `V4Osc3Macro5Amount6` | `0.5` |
| `V4Osc3Macro5Dest1` | `0` → Off |
| `V4Osc3Macro5Dest2` | `0` → Off |
| `V4Osc3Macro5Dest3` | `0` → Off |
| `V4Osc3Macro5Dest4` | `0` → Off |
| `V4Osc3Macro5Dest5` | `0` → Off |
| `V4Osc3Macro5Dest6` | `0` → Off |
| `V4Osc3Macro5Name` | `0` → Bottom-R; `0.5` → Bottom-R; `1` → Bottom-R |
| `V4Osc3TemplateName` | `0` → Custom; `1` → Custom |
| `VcaPan` | `0.5` |
| `VelocityAmount` | `0`; `0.5` |
| `VoiceAllocationMode` | `0` → 16 Voices: Analog Preferred |
| `WheelAmount` | `0`; `0.68` |

## Anhang: v15-only Parameternamen (nicht in v8-Exporten) – gruppiert nach Präfix

### `4*` (1)

`4`

### `AfterTouchAttack*` (1)

`AfterTouchAttack`

### `AfterTouchDoPoly*` (1)

`AfterTouchDoPoly`

### `AfterTouchKey*` (1)

`AfterTouchKey`

### `AfterTouchRelease*` (1)

`AfterTouchRelease`

### `AfterTouchValue*` (1)

`AfterTouchValue`

### `ArpSeqToMidiOut*` (1)

`ArpSeqToMidiOut`

### `ButtonPress*` (1)

`ButtonPress`

### `CCGotMapped*` (1)

`CCGotMapped`

### `CVClockDivider*` (1)

`CVClockDivider`

### `CVRange*` (4)

`CV1Range`, `CV2Range`, `CV3Range`, `CV4Range`

### `CalibTouchVertical*` (1)

`CalibTouchVertical`

### `ChordLatch*` (1)

`ChordLatch`

### `CodecRecLevel*` (1)

`CodecRecLevel`

### `CoreSelectedVariation*` (1)

`CoreSelectedVariation`

### `Development*` (6)

`Development1`, `Development2`, `Development3`, `Development4`, `Development5`, `Development6`

### `DigiFormerKeytrack*` (1)

`DigiFormerKeytrack`

### `DigiFormerLevel*` (1)

`DigiFormerLevel`

### `DigiFormerPan*` (1)

`DigiFormerPan`

### `DigiFormerTilt*` (1)

`DigiFormerTilt`

### `EnvGroupSelect*` (1)

`EnvGroupSelect`

### `FXLanelLevel*` (3)

`FXLanel1Level`, `FXLanel2Level`, `FXLanel3Level`

### `FXLanelPan*` (3)

`FXLanel1Pan`, `FXLanel2Pan`, `FXLanel3Pan`

### `FXRouting*` (1)

`FXRouting`

### `FXTotalDryWet*` (1)

`FXTotalDryWet`

### `FilterDomain*` (1)

`FilterDomain`

### `FilterLevel*` (2)

`Filter2Level`, `FilterLevel`

### `FilterModel*` (2)

`Filter1Model`, `Filter2Model`

### `FilterPan*` (2)

`Filter2Pan`, `FilterPan`

### `FilterState*` (2)

`Filter2State`, `FilterState`

### `FilterType*` (1)

`Filter2Type`

### `FinalColor*` (1)

`FinalColor`

### `Flavour*` (1)

`Flavour`

### `FlavourEnv*` (1)

`FlavourEnv`

### `FlavourFilter*` (1)

`FlavourFilter`

### `FlavourOsc*` (3)

`FlavourOsc1`, `FlavourOsc2`, `FlavourOsc3`

### `FlavourPan*` (1)

`FlavourPan`

### `FlavourPitch*` (1)

`FlavourPitch`

### `FlavourTiming*` (1)

`FlavourTiming`

### `FlavourVol*` (1)

`FlavourVol`

### `FreeEnvAmount*` (3)

`FreeEnv1Amount`, `FreeEnv2Amount`, `FreeEnv3Amount`

### `FreeEnvVeloAmount*` (3)

`FreeEnv1VeloAmount`, `FreeEnv2VeloAmount`, `FreeEnv3VeloAmount`

### `GlobalOutRoutingOverride*` (1)

`GlobalOutRoutingOverride`

### `GlobalSendsAux*` (1)

`GlobalSendsAux`

### `GlobalSendsMain*` (1)

`GlobalSendsMain`

### `IRPadChange*` (1)

`IRPadChange`

### `IRPadChordsMap*` (2)

`IRPadChordsMap`, `IRPadChordsMap2`

### `IRPadChordsMode*` (1)

`IRPadChordsMode`

### `IRPadLatch*` (1)

`IRPadLatch`

### `IRPadLatchMap*` (1)

`IRPadLatchMap`

### `IRPadLatchMode*` (1)

`IRPadLatchMode`

### `IRPadMode*` (1)

`IRPadMode`

### `IRPadNotesMap*` (1)

`IRPadNotesMap`

### `IRPadOct*` (1)

`IRPadOct`

### `IRPadScale*` (1)

`IRPadScale`

### `IRPadScaleRoot*` (1)

`IRPadScaleRoot`

### `IRPadSelChordType*` (1)

`IRPadSelChordType`

### `IRPadSelChordVoicing*` (1)

`IRPadSelChordVoicing`

### `IRPadSelected*` (1)

`IRPadSelected`

### `IRPadSelectedNote*` (1)

`IRPadSelectedNote1`

### `IRPadSelectedNoteActive*` (1)

`IRPadSelectedNoteActive1`

### `IRPadTriggerAlgo*` (1)

`IRPadTriggerAlgo`

### `IRPadVelo*` (1)

`IRPadVelo`

### `KeymapNote*` (1)

`KeymapNote`

### `LFOSelect*` (1)

`LFOSelect`

### `LastNoteReleased*` (1)

`LastNoteReleased`

### `LastPressedKey*` (1)

`LastPressedKey`

### `LayerActive*` (1)

`LayerActive`

### `LayerMaxNote*` (1)

`LayerMaxNote`

### `LayerMinNote*` (1)

`LayerMinNote`

### `LfoPolarity*` (6)

`Lfo1Polarity`, `Lfo2Polarity`, `Lfo3Polarity`, `Lfo4Polarity`, `Lfo5Polarity`, `Lfo6Polarity`

### `LoadFeatureFilter*` (1)

`LoadFeatureFilter`

### `Macro*` (6)

`Macro1`, `Macro2`, `Macro3`, `Macro4`, `Macro5`, `Macro6`

### `MultiAllocMode*` (1)

`MultiAllocMode`

### `MultiArpMode*` (1)

`MultiArpMode`

### `MutatorAllAmount*` (1)

`MutatorAllAmount`

### `MutatorEffectsAmount*` (1)

`MutatorEffectsAmount`

### `MutatorEnvelopesAmount*` (1)

`MutatorEnvelopesAmount`

### `MutatorFilterAmount*` (1)

`MutatorFilterAmount`

### `MutatorModulationAmount*` (1)

`MutatorModulationAmount`

### `MutatorOscAmount*` (1)

`MutatorOscAmount`

### `MutatorPitchAmount*` (1)

`MutatorPitchAmount`

### `OscForceRetrigger*` (3)

`Osc1ForceRetrigger`, `Osc2ForceRetrigger`, `Osc3ForceRetrigger`

### `OscMaxNote*` (3)

`Osc1MaxNote`, `Osc2MaxNote`, `Osc3MaxNote`

### `OscMinNote*` (3)

`Osc1MinNote`, `Osc2MinNote`, `Osc3MinNote`

### `PadCcNumX*` (1)

`Pad1CcNumX`

### `PadCcNumY*` (1)

`Pad1CcNumY`

### `ParamLockItem*` (1)

`ParamLockItem`

### `ParamLockNote*` (1)

`ParamLockNote`

### `PerNotePitchBend*` (1)

`PerNotePitchBend`

### `PolyArpFollow*` (1)

`PolyArpFollow`

### `PolyArpLines*` (1)

`PolyArpLines`

### `PolyArpMode*` (1)

`PolyArpMode`

### `PolyArpSkip*` (1)

`PolyArpSkip`

### `PolyArpTranspose*` (1)

`PolyArpTranspose`

### `PotModSrc*` (4)

`Pot1ModSrc`, `Pot2ModSrc`, `Pot3ModSrc`, `Pot4ModSrc`

### `PotParam*` (4)

`Pot1Param`, `Pot2Param`, `Pot3Param`, `Pot4Param`

### `PotPolarity*` (4)

`Pot1Polarity`, `Pot2Polarity`, `Pot3Polarity`, `Pot4Polarity`

### `RecordingSource*` (1)

`RecordingSource`

### `RecordingTrigger*` (1)

`RecordingTrigger`

### `ReverbModDepth*` (1)

`ReverbModDepth`

### `ReverbModRate*` (1)

`ReverbModRate`

### `ReverbXFade*` (1)

`ReverbXFade`

### `SeedsOscCount*` (3)

`SeedsOsc1Count`, `SeedsOsc2Count`, `SeedsOsc3Count`

### `SeedsOscDetune*` (3)

`SeedsOsc1Detune`, `SeedsOsc2Detune`, `SeedsOsc3Detune`

### `SeedsOscEnvAmount*` (3)

`SeedsOsc1EnvAmount`, `SeedsOsc2EnvAmount`, `SeedsOsc3EnvAmount`

### `SeedsOscNumVectors*` (3)

`SeedsOsc1NumVectors`, `SeedsOsc2NumVectors`, `SeedsOsc3NumVectors`

### `SeedsOscPosition*` (3)

`SeedsOsc1Position`, `SeedsOsc2Position`, `SeedsOsc3Position`

### `SeedsOscSoloVector*` (3)

`SeedsOsc1SoloVector`, `SeedsOsc2SoloVector`, `SeedsOsc3SoloVector`

### `SeedsOscSpread*` (3)

`SeedsOsc1Spread`, `SeedsOsc2Spread`, `SeedsOsc3Spread`

### `SeedsOscVecDirtType*` (36)

`SeedsOsc1Vec10DirtType`, `SeedsOsc1Vec11DirtType`, `SeedsOsc1Vec12DirtType`, `SeedsOsc1Vec1DirtType`, `SeedsOsc1Vec2DirtType`, `SeedsOsc1Vec3DirtType`, `SeedsOsc1Vec4DirtType`, `SeedsOsc1Vec5DirtType`, `SeedsOsc1Vec6DirtType`, `SeedsOsc1Vec7DirtType`, `SeedsOsc1Vec8DirtType`, `SeedsOsc1Vec9DirtType`, `SeedsOsc2Vec10DirtType`, `SeedsOsc2Vec11DirtType`, `SeedsOsc2Vec12DirtType`, `SeedsOsc2Vec1DirtType`, `SeedsOsc2Vec2DirtType`, `SeedsOsc2Vec3DirtType`, `SeedsOsc2Vec4DirtType`, `SeedsOsc2Vec5DirtType`, `SeedsOsc2Vec6DirtType`, `SeedsOsc2Vec7DirtType`, `SeedsOsc2Vec8DirtType`, `SeedsOsc2Vec9DirtType`, `SeedsOsc3Vec10DirtType`, `SeedsOsc3Vec11DirtType`, `SeedsOsc3Vec12DirtType`, `SeedsOsc3Vec1DirtType`, `SeedsOsc3Vec2DirtType`, `SeedsOsc3Vec3DirtType`, `SeedsOsc3Vec4DirtType`, `SeedsOsc3Vec5DirtType`, `SeedsOsc3Vec6DirtType`, `SeedsOsc3Vec7DirtType`, `SeedsOsc3Vec8DirtType`, `SeedsOsc3Vec9DirtType`

### `SeedsOscVecFMFeedback*` (36)

`SeedsOsc1Vec10FMFeedback`, `SeedsOsc1Vec11FMFeedback`, `SeedsOsc1Vec12FMFeedback`, `SeedsOsc1Vec1FMFeedback`, `SeedsOsc1Vec2FMFeedback`, `SeedsOsc1Vec3FMFeedback`, `SeedsOsc1Vec4FMFeedback`, `SeedsOsc1Vec5FMFeedback`, `SeedsOsc1Vec6FMFeedback`, `SeedsOsc1Vec7FMFeedback`, `SeedsOsc1Vec8FMFeedback`, `SeedsOsc1Vec9FMFeedback`, `SeedsOsc2Vec10FMFeedback`, `SeedsOsc2Vec11FMFeedback`, `SeedsOsc2Vec12FMFeedback`, `SeedsOsc2Vec1FMFeedback`, `SeedsOsc2Vec2FMFeedback`, `SeedsOsc2Vec3FMFeedback`, `SeedsOsc2Vec4FMFeedback`, `SeedsOsc2Vec5FMFeedback`, `SeedsOsc2Vec6FMFeedback`, `SeedsOsc2Vec7FMFeedback`, `SeedsOsc2Vec8FMFeedback`, `SeedsOsc2Vec9FMFeedback`, `SeedsOsc3Vec10FMFeedback`, `SeedsOsc3Vec11FMFeedback`, `SeedsOsc3Vec12FMFeedback`, `SeedsOsc3Vec1FMFeedback`, `SeedsOsc3Vec2FMFeedback`, `SeedsOsc3Vec3FMFeedback`, `SeedsOsc3Vec4FMFeedback`, `SeedsOsc3Vec5FMFeedback`, `SeedsOsc3Vec6FMFeedback`, `SeedsOsc3Vec7FMFeedback`, `SeedsOsc3Vec8FMFeedback`, `SeedsOsc3Vec9FMFeedback`

### `SeedsOscVecFMIndex*` (36)

`SeedsOsc1Vec10FMIndex`, `SeedsOsc1Vec11FMIndex`, `SeedsOsc1Vec12FMIndex`, `SeedsOsc1Vec1FMIndex`, `SeedsOsc1Vec2FMIndex`, `SeedsOsc1Vec3FMIndex`, `SeedsOsc1Vec4FMIndex`, `SeedsOsc1Vec5FMIndex`, `SeedsOsc1Vec6FMIndex`, `SeedsOsc1Vec7FMIndex`, `SeedsOsc1Vec8FMIndex`, `SeedsOsc1Vec9FMIndex`, `SeedsOsc2Vec10FMIndex`, `SeedsOsc2Vec11FMIndex`, `SeedsOsc2Vec12FMIndex`, `SeedsOsc2Vec1FMIndex`, `SeedsOsc2Vec2FMIndex`, `SeedsOsc2Vec3FMIndex`, `SeedsOsc2Vec4FMIndex`, `SeedsOsc2Vec5FMIndex`, `SeedsOsc2Vec6FMIndex`, `SeedsOsc2Vec7FMIndex`, `SeedsOsc2Vec8FMIndex`, `SeedsOsc2Vec9FMIndex`, `SeedsOsc3Vec10FMIndex`, `SeedsOsc3Vec11FMIndex`, `SeedsOsc3Vec12FMIndex`, `SeedsOsc3Vec1FMIndex`, `SeedsOsc3Vec2FMIndex`, `SeedsOsc3Vec3FMIndex`, `SeedsOsc3Vec4FMIndex`, `SeedsOsc3Vec5FMIndex`, `SeedsOsc3Vec6FMIndex`, `SeedsOsc3Vec7FMIndex`, `SeedsOsc3Vec8FMIndex`, `SeedsOsc3Vec9FMIndex`

### `SeedsOscVecFMRatio*` (36)

`SeedsOsc1Vec10FMRatio`, `SeedsOsc1Vec11FMRatio`, `SeedsOsc1Vec12FMRatio`, `SeedsOsc1Vec1FMRatio`, `SeedsOsc1Vec2FMRatio`, `SeedsOsc1Vec3FMRatio`, `SeedsOsc1Vec4FMRatio`, `SeedsOsc1Vec5FMRatio`, `SeedsOsc1Vec6FMRatio`, `SeedsOsc1Vec7FMRatio`, `SeedsOsc1Vec8FMRatio`, `SeedsOsc1Vec9FMRatio`, `SeedsOsc2Vec10FMRatio`, `SeedsOsc2Vec11FMRatio`, `SeedsOsc2Vec12FMRatio`, `SeedsOsc2Vec1FMRatio`, `SeedsOsc2Vec2FMRatio`, `SeedsOsc2Vec3FMRatio`, `SeedsOsc2Vec4FMRatio`, `SeedsOsc2Vec5FMRatio`, `SeedsOsc2Vec6FMRatio`, `SeedsOsc2Vec7FMRatio`, `SeedsOsc2Vec8FMRatio`, `SeedsOsc2Vec9FMRatio`, `SeedsOsc3Vec10FMRatio`, `SeedsOsc3Vec11FMRatio`, `SeedsOsc3Vec12FMRatio`, `SeedsOsc3Vec1FMRatio`, `SeedsOsc3Vec2FMRatio`, `SeedsOsc3Vec3FMRatio`, `SeedsOsc3Vec4FMRatio`, `SeedsOsc3Vec5FMRatio`, `SeedsOsc3Vec6FMRatio`, `SeedsOsc3Vec7FMRatio`, `SeedsOsc3Vec8FMRatio`, `SeedsOsc3Vec9FMRatio`

### `SeedsOscVecFreqRatioPart*` (144)

`SeedsOsc1Vec10FreqRatioPart1`, `SeedsOsc1Vec10FreqRatioPart2`, `SeedsOsc1Vec10FreqRatioPart3`, `SeedsOsc1Vec10FreqRatioPart4`, `SeedsOsc1Vec11FreqRatioPart1`, `SeedsOsc1Vec11FreqRatioPart2`, `SeedsOsc1Vec11FreqRatioPart3`, `SeedsOsc1Vec11FreqRatioPart4`, `SeedsOsc1Vec12FreqRatioPart1`, `SeedsOsc1Vec12FreqRatioPart2`, `SeedsOsc1Vec12FreqRatioPart3`, `SeedsOsc1Vec12FreqRatioPart4`, `SeedsOsc1Vec1FreqRatioPart1`, `SeedsOsc1Vec1FreqRatioPart2`, `SeedsOsc1Vec1FreqRatioPart3`, `SeedsOsc1Vec1FreqRatioPart4`, `SeedsOsc1Vec2FreqRatioPart1`, `SeedsOsc1Vec2FreqRatioPart2`, `SeedsOsc1Vec2FreqRatioPart3`, `SeedsOsc1Vec2FreqRatioPart4`, `SeedsOsc1Vec3FreqRatioPart1`, `SeedsOsc1Vec3FreqRatioPart2`, `SeedsOsc1Vec3FreqRatioPart3`, `SeedsOsc1Vec3FreqRatioPart4`, `SeedsOsc1Vec4FreqRatioPart1`, `SeedsOsc1Vec4FreqRatioPart2`, `SeedsOsc1Vec4FreqRatioPart3`, `SeedsOsc1Vec4FreqRatioPart4`, `SeedsOsc1Vec5FreqRatioPart1`, `SeedsOsc1Vec5FreqRatioPart2`, `SeedsOsc1Vec5FreqRatioPart3`, `SeedsOsc1Vec5FreqRatioPart4`, `SeedsOsc1Vec6FreqRatioPart1`, `SeedsOsc1Vec6FreqRatioPart2`, `SeedsOsc1Vec6FreqRatioPart3`, `SeedsOsc1Vec6FreqRatioPart4`, `SeedsOsc1Vec7FreqRatioPart1`, `SeedsOsc1Vec7FreqRatioPart2`, `SeedsOsc1Vec7FreqRatioPart3`, `SeedsOsc1Vec7FreqRatioPart4`, `SeedsOsc1Vec8FreqRatioPart1`, `SeedsOsc1Vec8FreqRatioPart2`, `SeedsOsc1Vec8FreqRatioPart3`, `SeedsOsc1Vec8FreqRatioPart4`, `SeedsOsc1Vec9FreqRatioPart1`, `SeedsOsc1Vec9FreqRatioPart2`, `SeedsOsc1Vec9FreqRatioPart3`, `SeedsOsc1Vec9FreqRatioPart4`, `SeedsOsc2Vec10FreqRatioPart1`, `SeedsOsc2Vec10FreqRatioPart2`, `SeedsOsc2Vec10FreqRatioPart3`, `SeedsOsc2Vec10FreqRatioPart4`, `SeedsOsc2Vec11FreqRatioPart1`, `SeedsOsc2Vec11FreqRatioPart2`, `SeedsOsc2Vec11FreqRatioPart3`, `SeedsOsc2Vec11FreqRatioPart4`, `SeedsOsc2Vec12FreqRatioPart1`, `SeedsOsc2Vec12FreqRatioPart2`, `SeedsOsc2Vec12FreqRatioPart3`, `SeedsOsc2Vec12FreqRatioPart4`, `SeedsOsc2Vec1FreqRatioPart1`, `SeedsOsc2Vec1FreqRatioPart2`, `SeedsOsc2Vec1FreqRatioPart3`, `SeedsOsc2Vec1FreqRatioPart4`, `SeedsOsc2Vec2FreqRatioPart1`, `SeedsOsc2Vec2FreqRatioPart2`, `SeedsOsc2Vec2FreqRatioPart3`, `SeedsOsc2Vec2FreqRatioPart4`, `SeedsOsc2Vec3FreqRatioPart1`, `SeedsOsc2Vec3FreqRatioPart2`, `SeedsOsc2Vec3FreqRatioPart3`, `SeedsOsc2Vec3FreqRatioPart4`, `SeedsOsc2Vec4FreqRatioPart1`, `SeedsOsc2Vec4FreqRatioPart2`, `SeedsOsc2Vec4FreqRatioPart3`, `SeedsOsc2Vec4FreqRatioPart4`, `SeedsOsc2Vec5FreqRatioPart1`, `SeedsOsc2Vec5FreqRatioPart2`, `SeedsOsc2Vec5FreqRatioPart3`, `SeedsOsc2Vec5FreqRatioPart4`, `SeedsOsc2Vec6FreqRatioPart1`, `SeedsOsc2Vec6FreqRatioPart2`, `SeedsOsc2Vec6FreqRatioPart3`, `SeedsOsc2Vec6FreqRatioPart4`, `SeedsOsc2Vec7FreqRatioPart1`, `SeedsOsc2Vec7FreqRatioPart2`, `SeedsOsc2Vec7FreqRatioPart3`, `SeedsOsc2Vec7FreqRatioPart4`, `SeedsOsc2Vec8FreqRatioPart1`, `SeedsOsc2Vec8FreqRatioPart2`, `SeedsOsc2Vec8FreqRatioPart3`, `SeedsOsc2Vec8FreqRatioPart4`, `SeedsOsc2Vec9FreqRatioPart1`, `SeedsOsc2Vec9FreqRatioPart2`, `SeedsOsc2Vec9FreqRatioPart3`, `SeedsOsc2Vec9FreqRatioPart4`, `SeedsOsc3Vec10FreqRatioPart1`, `SeedsOsc3Vec10FreqRatioPart2`, `SeedsOsc3Vec10FreqRatioPart3`, `SeedsOsc3Vec10FreqRatioPart4`, `SeedsOsc3Vec11FreqRatioPart1`, `SeedsOsc3Vec11FreqRatioPart2`, `SeedsOsc3Vec11FreqRatioPart3`, `SeedsOsc3Vec11FreqRatioPart4`, `SeedsOsc3Vec12FreqRatioPart1`, `SeedsOsc3Vec12FreqRatioPart2`, `SeedsOsc3Vec12FreqRatioPart3`, `SeedsOsc3Vec12FreqRatioPart4`, `SeedsOsc3Vec1FreqRatioPart1`, `SeedsOsc3Vec1FreqRatioPart2`, `SeedsOsc3Vec1FreqRatioPart3`, `SeedsOsc3Vec1FreqRatioPart4`, `SeedsOsc3Vec2FreqRatioPart1`, `SeedsOsc3Vec2FreqRatioPart2`, `SeedsOsc3Vec2FreqRatioPart3`, `SeedsOsc3Vec2FreqRatioPart4`, `SeedsOsc3Vec3FreqRatioPart1`, `SeedsOsc3Vec3FreqRatioPart2`, `SeedsOsc3Vec3FreqRatioPart3`, `SeedsOsc3Vec3FreqRatioPart4`, `SeedsOsc3Vec4FreqRatioPart1`, `SeedsOsc3Vec4FreqRatioPart2`, `SeedsOsc3Vec4FreqRatioPart3`, `SeedsOsc3Vec4FreqRatioPart4`, `SeedsOsc3Vec5FreqRatioPart1`, `SeedsOsc3Vec5FreqRatioPart2`, `SeedsOsc3Vec5FreqRatioPart3`, `SeedsOsc3Vec5FreqRatioPart4`, `SeedsOsc3Vec6FreqRatioPart1`, `SeedsOsc3Vec6FreqRatioPart2`, `SeedsOsc3Vec6FreqRatioPart3`, `SeedsOsc3Vec6FreqRatioPart4`, `SeedsOsc3Vec7FreqRatioPart1`, `SeedsOsc3Vec7FreqRatioPart2`, `SeedsOsc3Vec7FreqRatioPart3`, `SeedsOsc3Vec7FreqRatioPart4`, `SeedsOsc3Vec8FreqRatioPart1`, `SeedsOsc3Vec8FreqRatioPart2`, `SeedsOsc3Vec8FreqRatioPart3`, `SeedsOsc3Vec8FreqRatioPart4`, `SeedsOsc3Vec9FreqRatioPart1`, `SeedsOsc3Vec9FreqRatioPart2`, `SeedsOsc3Vec9FreqRatioPart3`, `SeedsOsc3Vec9FreqRatioPart4`

### `SeedsOscVecRMRatio*` (36)

`SeedsOsc1Vec10RMRatio`, `SeedsOsc1Vec11RMRatio`, `SeedsOsc1Vec12RMRatio`, `SeedsOsc1Vec1RMRatio`, `SeedsOsc1Vec2RMRatio`, `SeedsOsc1Vec3RMRatio`, `SeedsOsc1Vec4RMRatio`, `SeedsOsc1Vec5RMRatio`, `SeedsOsc1Vec6RMRatio`, `SeedsOsc1Vec7RMRatio`, `SeedsOsc1Vec8RMRatio`, `SeedsOsc1Vec9RMRatio`, `SeedsOsc2Vec10RMRatio`, `SeedsOsc2Vec11RMRatio`, `SeedsOsc2Vec12RMRatio`, `SeedsOsc2Vec1RMRatio`, `SeedsOsc2Vec2RMRatio`, `SeedsOsc2Vec3RMRatio`, `SeedsOsc2Vec4RMRatio`, `SeedsOsc2Vec5RMRatio`, `SeedsOsc2Vec6RMRatio`, `SeedsOsc2Vec7RMRatio`, `SeedsOsc2Vec8RMRatio`, `SeedsOsc2Vec9RMRatio`, `SeedsOsc3Vec10RMRatio`, `SeedsOsc3Vec11RMRatio`, `SeedsOsc3Vec12RMRatio`, `SeedsOsc3Vec1RMRatio`, `SeedsOsc3Vec2RMRatio`, `SeedsOsc3Vec3RMRatio`, `SeedsOsc3Vec4RMRatio`, `SeedsOsc3Vec5RMRatio`, `SeedsOsc3Vec6RMRatio`, `SeedsOsc3Vec7RMRatio`, `SeedsOsc3Vec8RMRatio`, `SeedsOsc3Vec9RMRatio`

### `SeedsOscVecSeedType*` (36)

`SeedsOsc1Vec10SeedType`, `SeedsOsc1Vec11SeedType`, `SeedsOsc1Vec12SeedType`, `SeedsOsc1Vec1SeedType`, `SeedsOsc1Vec2SeedType`, `SeedsOsc1Vec3SeedType`, `SeedsOsc1Vec4SeedType`, `SeedsOsc1Vec5SeedType`, `SeedsOsc1Vec6SeedType`, `SeedsOsc1Vec7SeedType`, `SeedsOsc1Vec8SeedType`, `SeedsOsc1Vec9SeedType`, `SeedsOsc2Vec10SeedType`, `SeedsOsc2Vec11SeedType`, `SeedsOsc2Vec12SeedType`, `SeedsOsc2Vec1SeedType`, `SeedsOsc2Vec2SeedType`, `SeedsOsc2Vec3SeedType`, `SeedsOsc2Vec4SeedType`, `SeedsOsc2Vec5SeedType`, `SeedsOsc2Vec6SeedType`, `SeedsOsc2Vec7SeedType`, `SeedsOsc2Vec8SeedType`, `SeedsOsc2Vec9SeedType`, `SeedsOsc3Vec10SeedType`, `SeedsOsc3Vec11SeedType`, `SeedsOsc3Vec12SeedType`, `SeedsOsc3Vec1SeedType`, `SeedsOsc3Vec2SeedType`, `SeedsOsc3Vec3SeedType`, `SeedsOsc3Vec4SeedType`, `SeedsOsc3Vec5SeedType`, `SeedsOsc3Vec6SeedType`, `SeedsOsc3Vec7SeedType`, `SeedsOsc3Vec8SeedType`, `SeedsOsc3Vec9SeedType`

### `SeedsOscVecTranspose*` (36)

`SeedsOsc1Vec10Transpose`, `SeedsOsc1Vec11Transpose`, `SeedsOsc1Vec12Transpose`, `SeedsOsc1Vec1Transpose`, `SeedsOsc1Vec2Transpose`, `SeedsOsc1Vec3Transpose`, `SeedsOsc1Vec4Transpose`, `SeedsOsc1Vec5Transpose`, `SeedsOsc1Vec6Transpose`, `SeedsOsc1Vec7Transpose`, `SeedsOsc1Vec8Transpose`, `SeedsOsc1Vec9Transpose`, `SeedsOsc2Vec10Transpose`, `SeedsOsc2Vec11Transpose`, `SeedsOsc2Vec12Transpose`, `SeedsOsc2Vec1Transpose`, `SeedsOsc2Vec2Transpose`, `SeedsOsc2Vec3Transpose`, `SeedsOsc2Vec4Transpose`, `SeedsOsc2Vec5Transpose`, `SeedsOsc2Vec6Transpose`, `SeedsOsc2Vec7Transpose`, `SeedsOsc2Vec8Transpose`, `SeedsOsc2Vec9Transpose`, `SeedsOsc3Vec10Transpose`, `SeedsOsc3Vec11Transpose`, `SeedsOsc3Vec12Transpose`, `SeedsOsc3Vec1Transpose`, `SeedsOsc3Vec2Transpose`, `SeedsOsc3Vec3Transpose`, `SeedsOsc3Vec4Transpose`, `SeedsOsc3Vec5Transpose`, `SeedsOsc3Vec6Transpose`, `SeedsOsc3Vec7Transpose`, `SeedsOsc3Vec8Transpose`, `SeedsOsc3Vec9Transpose`

### `SeedsOscVecVolPart*` (144)

`SeedsOsc1Vec10VolPart1`, `SeedsOsc1Vec10VolPart2`, `SeedsOsc1Vec10VolPart3`, `SeedsOsc1Vec10VolPart4`, `SeedsOsc1Vec11VolPart1`, `SeedsOsc1Vec11VolPart2`, `SeedsOsc1Vec11VolPart3`, `SeedsOsc1Vec11VolPart4`, `SeedsOsc1Vec12VolPart1`, `SeedsOsc1Vec12VolPart2`, `SeedsOsc1Vec12VolPart3`, `SeedsOsc1Vec12VolPart4`, `SeedsOsc1Vec1VolPart1`, `SeedsOsc1Vec1VolPart2`, `SeedsOsc1Vec1VolPart3`, `SeedsOsc1Vec1VolPart4`, `SeedsOsc1Vec2VolPart1`, `SeedsOsc1Vec2VolPart2`, `SeedsOsc1Vec2VolPart3`, `SeedsOsc1Vec2VolPart4`, `SeedsOsc1Vec3VolPart1`, `SeedsOsc1Vec3VolPart2`, `SeedsOsc1Vec3VolPart3`, `SeedsOsc1Vec3VolPart4`, `SeedsOsc1Vec4VolPart1`, `SeedsOsc1Vec4VolPart2`, `SeedsOsc1Vec4VolPart3`, `SeedsOsc1Vec4VolPart4`, `SeedsOsc1Vec5VolPart1`, `SeedsOsc1Vec5VolPart2`, `SeedsOsc1Vec5VolPart3`, `SeedsOsc1Vec5VolPart4`, `SeedsOsc1Vec6VolPart1`, `SeedsOsc1Vec6VolPart2`, `SeedsOsc1Vec6VolPart3`, `SeedsOsc1Vec6VolPart4`, `SeedsOsc1Vec7VolPart1`, `SeedsOsc1Vec7VolPart2`, `SeedsOsc1Vec7VolPart3`, `SeedsOsc1Vec7VolPart4`, `SeedsOsc1Vec8VolPart1`, `SeedsOsc1Vec8VolPart2`, `SeedsOsc1Vec8VolPart3`, `SeedsOsc1Vec8VolPart4`, `SeedsOsc1Vec9VolPart1`, `SeedsOsc1Vec9VolPart2`, `SeedsOsc1Vec9VolPart3`, `SeedsOsc1Vec9VolPart4`, `SeedsOsc2Vec10VolPart1`, `SeedsOsc2Vec10VolPart2`, `SeedsOsc2Vec10VolPart3`, `SeedsOsc2Vec10VolPart4`, `SeedsOsc2Vec11VolPart1`, `SeedsOsc2Vec11VolPart2`, `SeedsOsc2Vec11VolPart3`, `SeedsOsc2Vec11VolPart4`, `SeedsOsc2Vec12VolPart1`, `SeedsOsc2Vec12VolPart2`, `SeedsOsc2Vec12VolPart3`, `SeedsOsc2Vec12VolPart4`, `SeedsOsc2Vec1VolPart1`, `SeedsOsc2Vec1VolPart2`, `SeedsOsc2Vec1VolPart3`, `SeedsOsc2Vec1VolPart4`, `SeedsOsc2Vec2VolPart1`, `SeedsOsc2Vec2VolPart2`, `SeedsOsc2Vec2VolPart3`, `SeedsOsc2Vec2VolPart4`, `SeedsOsc2Vec3VolPart1`, `SeedsOsc2Vec3VolPart2`, `SeedsOsc2Vec3VolPart3`, `SeedsOsc2Vec3VolPart4`, `SeedsOsc2Vec4VolPart1`, `SeedsOsc2Vec4VolPart2`, `SeedsOsc2Vec4VolPart3`, `SeedsOsc2Vec4VolPart4`, `SeedsOsc2Vec5VolPart1`, `SeedsOsc2Vec5VolPart2`, `SeedsOsc2Vec5VolPart3`, `SeedsOsc2Vec5VolPart4`, `SeedsOsc2Vec6VolPart1`, `SeedsOsc2Vec6VolPart2`, `SeedsOsc2Vec6VolPart3`, `SeedsOsc2Vec6VolPart4`, `SeedsOsc2Vec7VolPart1`, `SeedsOsc2Vec7VolPart2`, `SeedsOsc2Vec7VolPart3`, `SeedsOsc2Vec7VolPart4`, `SeedsOsc2Vec8VolPart1`, `SeedsOsc2Vec8VolPart2`, `SeedsOsc2Vec8VolPart3`, `SeedsOsc2Vec8VolPart4`, `SeedsOsc2Vec9VolPart1`, `SeedsOsc2Vec9VolPart2`, `SeedsOsc2Vec9VolPart3`, `SeedsOsc2Vec9VolPart4`, `SeedsOsc3Vec10VolPart1`, `SeedsOsc3Vec10VolPart2`, `SeedsOsc3Vec10VolPart3`, `SeedsOsc3Vec10VolPart4`, `SeedsOsc3Vec11VolPart1`, `SeedsOsc3Vec11VolPart2`, `SeedsOsc3Vec11VolPart3`, `SeedsOsc3Vec11VolPart4`, `SeedsOsc3Vec12VolPart1`, `SeedsOsc3Vec12VolPart2`, `SeedsOsc3Vec12VolPart3`, `SeedsOsc3Vec12VolPart4`, `SeedsOsc3Vec1VolPart1`, `SeedsOsc3Vec1VolPart2`, `SeedsOsc3Vec1VolPart3`, `SeedsOsc3Vec1VolPart4`, `SeedsOsc3Vec2VolPart1`, `SeedsOsc3Vec2VolPart2`, `SeedsOsc3Vec2VolPart3`, `SeedsOsc3Vec2VolPart4`, `SeedsOsc3Vec3VolPart1`, `SeedsOsc3Vec3VolPart2`, `SeedsOsc3Vec3VolPart3`, `SeedsOsc3Vec3VolPart4`, `SeedsOsc3Vec4VolPart1`, `SeedsOsc3Vec4VolPart2`, `SeedsOsc3Vec4VolPart3`, `SeedsOsc3Vec4VolPart4`, `SeedsOsc3Vec5VolPart1`, `SeedsOsc3Vec5VolPart2`, `SeedsOsc3Vec5VolPart3`, `SeedsOsc3Vec5VolPart4`, `SeedsOsc3Vec6VolPart1`, `SeedsOsc3Vec6VolPart2`, `SeedsOsc3Vec6VolPart3`, `SeedsOsc3Vec6VolPart4`, `SeedsOsc3Vec7VolPart1`, `SeedsOsc3Vec7VolPart2`, `SeedsOsc3Vec7VolPart3`, `SeedsOsc3Vec7VolPart4`, `SeedsOsc3Vec8VolPart1`, `SeedsOsc3Vec8VolPart2`, `SeedsOsc3Vec8VolPart3`, `SeedsOsc3Vec8VolPart4`, `SeedsOsc3Vec9VolPart1`, `SeedsOsc3Vec9VolPart2`, `SeedsOsc3Vec9VolPart3`, `SeedsOsc3Vec9VolPart4`

### `SeedsOscVecVolume*` (36)

`SeedsOsc1Vec10Volume`, `SeedsOsc1Vec11Volume`, `SeedsOsc1Vec12Volume`, `SeedsOsc1Vec1Volume`, `SeedsOsc1Vec2Volume`, `SeedsOsc1Vec3Volume`, `SeedsOsc1Vec4Volume`, `SeedsOsc1Vec5Volume`, `SeedsOsc1Vec6Volume`, `SeedsOsc1Vec7Volume`, `SeedsOsc1Vec8Volume`, `SeedsOsc1Vec9Volume`, `SeedsOsc2Vec10Volume`, `SeedsOsc2Vec11Volume`, `SeedsOsc2Vec12Volume`, `SeedsOsc2Vec1Volume`, `SeedsOsc2Vec2Volume`, `SeedsOsc2Vec3Volume`, `SeedsOsc2Vec4Volume`, `SeedsOsc2Vec5Volume`, `SeedsOsc2Vec6Volume`, `SeedsOsc2Vec7Volume`, `SeedsOsc2Vec8Volume`, `SeedsOsc2Vec9Volume`, `SeedsOsc3Vec10Volume`, `SeedsOsc3Vec11Volume`, `SeedsOsc3Vec12Volume`, `SeedsOsc3Vec1Volume`, `SeedsOsc3Vec2Volume`, `SeedsOsc3Vec3Volume`, `SeedsOsc3Vec4Volume`, `SeedsOsc3Vec5Volume`, `SeedsOsc3Vec6Volume`, `SeedsOsc3Vec7Volume`, `SeedsOsc3Vec8Volume`, `SeedsOsc3Vec9Volume`

### `SeedsOscVecWavetable*` (36)

`SeedsOsc1Vec10Wavetable`, `SeedsOsc1Vec11Wavetable`, `SeedsOsc1Vec12Wavetable`, `SeedsOsc1Vec1Wavetable`, `SeedsOsc1Vec2Wavetable`, `SeedsOsc1Vec3Wavetable`, `SeedsOsc1Vec4Wavetable`, `SeedsOsc1Vec5Wavetable`, `SeedsOsc1Vec6Wavetable`, `SeedsOsc1Vec7Wavetable`, `SeedsOsc1Vec8Wavetable`, `SeedsOsc1Vec9Wavetable`, `SeedsOsc2Vec10Wavetable`, `SeedsOsc2Vec11Wavetable`, `SeedsOsc2Vec12Wavetable`, `SeedsOsc2Vec1Wavetable`, `SeedsOsc2Vec2Wavetable`, `SeedsOsc2Vec3Wavetable`, `SeedsOsc2Vec4Wavetable`, `SeedsOsc2Vec5Wavetable`, `SeedsOsc2Vec6Wavetable`, `SeedsOsc2Vec7Wavetable`, `SeedsOsc2Vec8Wavetable`, `SeedsOsc2Vec9Wavetable`, `SeedsOsc3Vec10Wavetable`, `SeedsOsc3Vec11Wavetable`, `SeedsOsc3Vec12Wavetable`, `SeedsOsc3Vec1Wavetable`, `SeedsOsc3Vec2Wavetable`, `SeedsOsc3Vec3Wavetable`, `SeedsOsc3Vec4Wavetable`, `SeedsOsc3Vec5Wavetable`, `SeedsOsc3Vec6Wavetable`, `SeedsOsc3Vec7Wavetable`, `SeedsOsc3Vec8Wavetable`, `SeedsOsc3Vec9Wavetable`

### `SeedsOscVecWavetablePos*` (36)

`SeedsOsc1Vec10WavetablePos`, `SeedsOsc1Vec11WavetablePos`, `SeedsOsc1Vec12WavetablePos`, `SeedsOsc1Vec1WavetablePos`, `SeedsOsc1Vec2WavetablePos`, `SeedsOsc1Vec3WavetablePos`, `SeedsOsc1Vec4WavetablePos`, `SeedsOsc1Vec5WavetablePos`, `SeedsOsc1Vec6WavetablePos`, `SeedsOsc1Vec7WavetablePos`, `SeedsOsc1Vec8WavetablePos`, `SeedsOsc1Vec9WavetablePos`, `SeedsOsc2Vec10WavetablePos`, `SeedsOsc2Vec11WavetablePos`, `SeedsOsc2Vec12WavetablePos`, `SeedsOsc2Vec1WavetablePos`, `SeedsOsc2Vec2WavetablePos`, `SeedsOsc2Vec3WavetablePos`, `SeedsOsc2Vec4WavetablePos`, `SeedsOsc2Vec5WavetablePos`, `SeedsOsc2Vec6WavetablePos`, `SeedsOsc2Vec7WavetablePos`, `SeedsOsc2Vec8WavetablePos`, `SeedsOsc2Vec9WavetablePos`, `SeedsOsc3Vec10WavetablePos`, `SeedsOsc3Vec11WavetablePos`, `SeedsOsc3Vec12WavetablePos`, `SeedsOsc3Vec1WavetablePos`, `SeedsOsc3Vec2WavetablePos`, `SeedsOsc3Vec3WavetablePos`, `SeedsOsc3Vec4WavetablePos`, `SeedsOsc3Vec5WavetablePos`, `SeedsOsc3Vec6WavetablePos`, `SeedsOsc3Vec7WavetablePos`, `SeedsOsc3Vec8WavetablePos`, `SeedsOsc3Vec9WavetablePos`

### `SeedsOscVecdirtReso*` (36)

`SeedsOsc1Vec10dirtReso`, `SeedsOsc1Vec11dirtReso`, `SeedsOsc1Vec12dirtReso`, `SeedsOsc1Vec1dirtReso`, `SeedsOsc1Vec2dirtReso`, `SeedsOsc1Vec3dirtReso`, `SeedsOsc1Vec4dirtReso`, `SeedsOsc1Vec5dirtReso`, `SeedsOsc1Vec6dirtReso`, `SeedsOsc1Vec7dirtReso`, `SeedsOsc1Vec8dirtReso`, `SeedsOsc1Vec9dirtReso`, `SeedsOsc2Vec10dirtReso`, `SeedsOsc2Vec11dirtReso`, `SeedsOsc2Vec12dirtReso`, `SeedsOsc2Vec1dirtReso`, `SeedsOsc2Vec2dirtReso`, `SeedsOsc2Vec3dirtReso`, `SeedsOsc2Vec4dirtReso`, `SeedsOsc2Vec5dirtReso`, `SeedsOsc2Vec6dirtReso`, `SeedsOsc2Vec7dirtReso`, `SeedsOsc2Vec8dirtReso`, `SeedsOsc2Vec9dirtReso`, `SeedsOsc3Vec10dirtReso`, `SeedsOsc3Vec11dirtReso`, `SeedsOsc3Vec12dirtReso`, `SeedsOsc3Vec1dirtReso`, `SeedsOsc3Vec2dirtReso`, `SeedsOsc3Vec3dirtReso`, `SeedsOsc3Vec4dirtReso`, `SeedsOsc3Vec5dirtReso`, `SeedsOsc3Vec6dirtReso`, `SeedsOsc3Vec7dirtReso`, `SeedsOsc3Vec8dirtReso`, `SeedsOsc3Vec9dirtReso`

### `SeedsOscVecdirtSpeed*` (36)

`SeedsOsc1Vec10dirtSpeed`, `SeedsOsc1Vec11dirtSpeed`, `SeedsOsc1Vec12dirtSpeed`, `SeedsOsc1Vec1dirtSpeed`, `SeedsOsc1Vec2dirtSpeed`, `SeedsOsc1Vec3dirtSpeed`, `SeedsOsc1Vec4dirtSpeed`, `SeedsOsc1Vec5dirtSpeed`, `SeedsOsc1Vec6dirtSpeed`, `SeedsOsc1Vec7dirtSpeed`, `SeedsOsc1Vec8dirtSpeed`, `SeedsOsc1Vec9dirtSpeed`, `SeedsOsc2Vec10dirtSpeed`, `SeedsOsc2Vec11dirtSpeed`, `SeedsOsc2Vec12dirtSpeed`, `SeedsOsc2Vec1dirtSpeed`, `SeedsOsc2Vec2dirtSpeed`, `SeedsOsc2Vec3dirtSpeed`, `SeedsOsc2Vec4dirtSpeed`, `SeedsOsc2Vec5dirtSpeed`, `SeedsOsc2Vec6dirtSpeed`, `SeedsOsc2Vec7dirtSpeed`, `SeedsOsc2Vec8dirtSpeed`, `SeedsOsc2Vec9dirtSpeed`, `SeedsOsc3Vec10dirtSpeed`, `SeedsOsc3Vec11dirtSpeed`, `SeedsOsc3Vec12dirtSpeed`, `SeedsOsc3Vec1dirtSpeed`, `SeedsOsc3Vec2dirtSpeed`, `SeedsOsc3Vec3dirtSpeed`, `SeedsOsc3Vec4dirtSpeed`, `SeedsOsc3Vec5dirtSpeed`, `SeedsOsc3Vec6dirtSpeed`, `SeedsOsc3Vec7dirtSpeed`, `SeedsOsc3Vec8dirtSpeed`, `SeedsOsc3Vec9dirtSpeed`

### `SelectedSampleDirection*` (1)

`SelectedSampleDirection`

### `SelectedSampleTrackPitch*` (1)

`SelectedSampleTrackPitch`

### `SelectedSampleXFade*` (1)

`SelectedSampleXFade`

### `SelectedSeedsOscPart*` (3)

`SelectedSeedsOsc1Part`, `SelectedSeedsOsc2Part`, `SelectedSeedsOsc3Part`

### `SelectedSeedsOscVector*` (3)

`SelectedSeedsOsc1Vector`, `SelectedSeedsOsc2Vector`, `SelectedSeedsOsc3Vector`

### `SelectedWaveKF*` (1)

`SelectedWaveKF`

### `SelectedWaveKFInterpol*` (1)

`SelectedWaveKFInterpol`

### `SelectedWaveKFProcParam*` (2)

`SelectedWaveKFProcParam1`, `SelectedWaveKFProcParam2`

### `SelectedWaveKFProcType*` (1)

`SelectedWaveKFProcType`

### `SelectedWaveKFSpecAmp*` (1)

`SelectedWaveKFSpecAmp`

### `SelectedWaveKFSpecBin*` (1)

`SelectedWaveKFSpecBin`

### `SelectedWaveKFType*` (1)

`SelectedWaveKFType`

### `SelectedWaveKFWaveType*` (1)

`SelectedWaveKFWaveType`

### `SelectedWavetableOscPos*` (3)

`SelectedWavetableOsc1Pos`, `SelectedWavetableOsc2Pos`, `SelectedWavetableOsc3Pos`

### `SeqStepGate*` (32)

`SeqStep33Gate`, `SeqStep34Gate`, `SeqStep35Gate`, `SeqStep36Gate`, `SeqStep37Gate`, `SeqStep38Gate`, `SeqStep39Gate`, `SeqStep40Gate`, `SeqStep41Gate`, `SeqStep42Gate`, `SeqStep43Gate`, `SeqStep44Gate`, `SeqStep45Gate`, `SeqStep46Gate`, `SeqStep47Gate`, `SeqStep48Gate`, `SeqStep49Gate`, `SeqStep50Gate`, `SeqStep51Gate`, `SeqStep52Gate`, `SeqStep53Gate`, `SeqStep54Gate`, `SeqStep55Gate`, `SeqStep56Gate`, `SeqStep57Gate`, `SeqStep58Gate`, `SeqStep59Gate`, `SeqStep60Gate`, `SeqStep61Gate`, `SeqStep62Gate`, `SeqStep63Gate`, `SeqStep64Gate`

### `SeqStepParam*` (384)

`SeqStep10Param5`, `SeqStep10Param6`, `SeqStep10Param7`, `SeqStep10Param8`, `SeqStep11Param5`, `SeqStep11Param6`, `SeqStep11Param7`, `SeqStep11Param8`, `SeqStep12Param5`, `SeqStep12Param6`, `SeqStep12Param7`, `SeqStep12Param8`, `SeqStep13Param5`, `SeqStep13Param6`, `SeqStep13Param7`, `SeqStep13Param8`, `SeqStep14Param5`, `SeqStep14Param6`, `SeqStep14Param7`, `SeqStep14Param8`, `SeqStep15Param5`, `SeqStep15Param6`, `SeqStep15Param7`, `SeqStep15Param8`, `SeqStep16Param5`, `SeqStep16Param6`, `SeqStep16Param7`, `SeqStep16Param8`, `SeqStep17Param5`, `SeqStep17Param6`, `SeqStep17Param7`, `SeqStep17Param8`, `SeqStep18Param5`, `SeqStep18Param6`, `SeqStep18Param7`, `SeqStep18Param8`, `SeqStep19Param5`, `SeqStep19Param6`, `SeqStep19Param7`, `SeqStep19Param8`, `SeqStep1Param5`, `SeqStep1Param6`, `SeqStep1Param7`, `SeqStep1Param8`, `SeqStep20Param5`, `SeqStep20Param6`, `SeqStep20Param7`, `SeqStep20Param8`, `SeqStep21Param5`, `SeqStep21Param6`, `SeqStep21Param7`, `SeqStep21Param8`, `SeqStep22Param5`, `SeqStep22Param6`, `SeqStep22Param7`, `SeqStep22Param8`, `SeqStep23Param5`, `SeqStep23Param6`, `SeqStep23Param7`, `SeqStep23Param8`, `SeqStep24Param5`, `SeqStep24Param6`, `SeqStep24Param7`, `SeqStep24Param8`, `SeqStep25Param5`, `SeqStep25Param6`, `SeqStep25Param7`, `SeqStep25Param8`, `SeqStep26Param5`, `SeqStep26Param6`, `SeqStep26Param7`, `SeqStep26Param8`, `SeqStep27Param5`, `SeqStep27Param6`, `SeqStep27Param7`, `SeqStep27Param8`, `SeqStep28Param5`, `SeqStep28Param6`, `SeqStep28Param7`, `SeqStep28Param8`, `SeqStep29Param5`, `SeqStep29Param6`, `SeqStep29Param7`, `SeqStep29Param8`, `SeqStep2Param5`, `SeqStep2Param6`, `SeqStep2Param7`, `SeqStep2Param8`, `SeqStep30Param5`, `SeqStep30Param6`, `SeqStep30Param7`, `SeqStep30Param8`, `SeqStep31Param5`, `SeqStep31Param6`, `SeqStep31Param7`, `SeqStep31Param8`, `SeqStep32Param5`, `SeqStep32Param6`, `SeqStep32Param7`, `SeqStep32Param8`, `SeqStep33Param1`, `SeqStep33Param2`, `SeqStep33Param3`, `SeqStep33Param4`, `SeqStep33Param5`, `SeqStep33Param6`, `SeqStep33Param7`, `SeqStep33Param8`, `SeqStep34Param1`, `SeqStep34Param2`, `SeqStep34Param3`, `SeqStep34Param4`, `SeqStep34Param5`, `SeqStep34Param6`, `SeqStep34Param7`, `SeqStep34Param8`, `SeqStep35Param1`, `SeqStep35Param2`, `SeqStep35Param3`, `SeqStep35Param4`, `SeqStep35Param5`, `SeqStep35Param6`, `SeqStep35Param7`, `SeqStep35Param8`, `SeqStep36Param1`, `SeqStep36Param2`, `SeqStep36Param3`, `SeqStep36Param4`, `SeqStep36Param5`, `SeqStep36Param6`, `SeqStep36Param7`, `SeqStep36Param8`, `SeqStep37Param1`, `SeqStep37Param2`, `SeqStep37Param3`, `SeqStep37Param4`, `SeqStep37Param5`, `SeqStep37Param6`, `SeqStep37Param7`, `SeqStep37Param8`, `SeqStep38Param1`, `SeqStep38Param2`, `SeqStep38Param3`, `SeqStep38Param4`, `SeqStep38Param5`, `SeqStep38Param6`, `SeqStep38Param7`, `SeqStep38Param8`, `SeqStep39Param1`, `SeqStep39Param2`, `SeqStep39Param3`, `SeqStep39Param4`, `SeqStep39Param5`, `SeqStep39Param6`, `SeqStep39Param7`, `SeqStep39Param8`, `SeqStep3Param5`, `SeqStep3Param6`, `SeqStep3Param7`, `SeqStep3Param8`, `SeqStep40Param1`, `SeqStep40Param2`, `SeqStep40Param3`, `SeqStep40Param4`, `SeqStep40Param5`, `SeqStep40Param6`, `SeqStep40Param7`, `SeqStep40Param8`, `SeqStep41Param1`, `SeqStep41Param2`, `SeqStep41Param3`, `SeqStep41Param4`, `SeqStep41Param5`, `SeqStep41Param6`, `SeqStep41Param7`, `SeqStep41Param8`, `SeqStep42Param1`, `SeqStep42Param2`, `SeqStep42Param3`, `SeqStep42Param4`, `SeqStep42Param5`, `SeqStep42Param6`, `SeqStep42Param7`, `SeqStep42Param8`, `SeqStep43Param1`, `SeqStep43Param2`, `SeqStep43Param3`, `SeqStep43Param4`, `SeqStep43Param5`, `SeqStep43Param6`, `SeqStep43Param7`, `SeqStep43Param8`, `SeqStep44Param1`, `SeqStep44Param2`, `SeqStep44Param3`, `SeqStep44Param4`, `SeqStep44Param5`, `SeqStep44Param6`, `SeqStep44Param7`, `SeqStep44Param8`, `SeqStep45Param1`, `SeqStep45Param2`, `SeqStep45Param3`, `SeqStep45Param4`, `SeqStep45Param5`, `SeqStep45Param6`, `SeqStep45Param7`, `SeqStep45Param8`, `SeqStep46Param1`, `SeqStep46Param2`, `SeqStep46Param3`, `SeqStep46Param4`, `SeqStep46Param5`, `SeqStep46Param6`, `SeqStep46Param7`, `SeqStep46Param8`, `SeqStep47Param1`, `SeqStep47Param2`, `SeqStep47Param3`, `SeqStep47Param4`, `SeqStep47Param5`, `SeqStep47Param6`, `SeqStep47Param7`, `SeqStep47Param8`, `SeqStep48Param1`, `SeqStep48Param2`, `SeqStep48Param3`, `SeqStep48Param4`, `SeqStep48Param5`, `SeqStep48Param6`, `SeqStep48Param7`, `SeqStep48Param8`, `SeqStep49Param1`, `SeqStep49Param2`, `SeqStep49Param3`, `SeqStep49Param4`, `SeqStep49Param5`, `SeqStep49Param6`, `SeqStep49Param7`, `SeqStep49Param8`, `SeqStep4Param5`, `SeqStep4Param6`, `SeqStep4Param7`, `SeqStep4Param8`, `SeqStep50Param1`, `SeqStep50Param2`, `SeqStep50Param3`, `SeqStep50Param4`, `SeqStep50Param5`, `SeqStep50Param6`, `SeqStep50Param7`, `SeqStep50Param8`, `SeqStep51Param1`, `SeqStep51Param2`, `SeqStep51Param3`, `SeqStep51Param4`, `SeqStep51Param5`, `SeqStep51Param6`, `SeqStep51Param7`, `SeqStep51Param8`, `SeqStep52Param1`, `SeqStep52Param2`, `SeqStep52Param3`, `SeqStep52Param4`, `SeqStep52Param5`, `SeqStep52Param6`, `SeqStep52Param7`, `SeqStep52Param8`, `SeqStep53Param1`, `SeqStep53Param2`, `SeqStep53Param3`, `SeqStep53Param4`, `SeqStep53Param5`, `SeqStep53Param6`, `SeqStep53Param7`, `SeqStep53Param8`, `SeqStep54Param1`, `SeqStep54Param2`, `SeqStep54Param3`, `SeqStep54Param4`, `SeqStep54Param5`, `SeqStep54Param6`, `SeqStep54Param7`, `SeqStep54Param8`, `SeqStep55Param1`, `SeqStep55Param2`, `SeqStep55Param3`, `SeqStep55Param4`, `SeqStep55Param5`, `SeqStep55Param6`, `SeqStep55Param7`, `SeqStep55Param8`, `SeqStep56Param1`, `SeqStep56Param2`, `SeqStep56Param3`, `SeqStep56Param4`, `SeqStep56Param5`, `SeqStep56Param6`, `SeqStep56Param7`, `SeqStep56Param8`, `SeqStep57Param1`, `SeqStep57Param2`, `SeqStep57Param3`, `SeqStep57Param4`, `SeqStep57Param5`, `SeqStep57Param6`, `SeqStep57Param7`, `SeqStep57Param8`, `SeqStep58Param1`, `SeqStep58Param2`, `SeqStep58Param3`, `SeqStep58Param4`, `SeqStep58Param5`, `SeqStep58Param6`, `SeqStep58Param7`, `SeqStep58Param8`, `SeqStep59Param1`, `SeqStep59Param2`, `SeqStep59Param3`, `SeqStep59Param4`, `SeqStep59Param5`, `SeqStep59Param6`, `SeqStep59Param7`, `SeqStep59Param8`, `SeqStep5Param5`, `SeqStep5Param6`, `SeqStep5Param7`, `SeqStep5Param8`, `SeqStep60Param1`, `SeqStep60Param2`, `SeqStep60Param3`, `SeqStep60Param4`, `SeqStep60Param5`, `SeqStep60Param6`, `SeqStep60Param7`, `SeqStep60Param8`, `SeqStep61Param1`, `SeqStep61Param2`, `SeqStep61Param3`, `SeqStep61Param4`, `SeqStep61Param5`, `SeqStep61Param6`, `SeqStep61Param7`, `SeqStep61Param8`, `SeqStep62Param1`, `SeqStep62Param2`, `SeqStep62Param3`, `SeqStep62Param4`, `SeqStep62Param5`, `SeqStep62Param6`, `SeqStep62Param7`, `SeqStep62Param8`, `SeqStep63Param1`, `SeqStep63Param2`, `SeqStep63Param3`, `SeqStep63Param4`, `SeqStep63Param5`, `SeqStep63Param6`, `SeqStep63Param7`, `SeqStep63Param8`, `SeqStep64Param1`, `SeqStep64Param2`, `SeqStep64Param3`, `SeqStep64Param4`, `SeqStep64Param5`, `SeqStep64Param6`, `SeqStep64Param7`, `SeqStep64Param8`, `SeqStep6Param5`, `SeqStep6Param6`, `SeqStep6Param7`, `SeqStep6Param8`, `SeqStep7Param5`, `SeqStep7Param6`, `SeqStep7Param7`, `SeqStep7Param8`, `SeqStep8Param5`, `SeqStep8Param6`, `SeqStep8Param7`, `SeqStep8Param8`, `SeqStep9Param5`, `SeqStep9Param6`, `SeqStep9Param7`, `SeqStep9Param8`

### `SeqStepPitch*` (32)

`SeqStep33Pitch`, `SeqStep34Pitch`, `SeqStep35Pitch`, `SeqStep36Pitch`, `SeqStep37Pitch`, `SeqStep38Pitch`, `SeqStep39Pitch`, `SeqStep40Pitch`, `SeqStep41Pitch`, `SeqStep42Pitch`, `SeqStep43Pitch`, `SeqStep44Pitch`, `SeqStep45Pitch`, `SeqStep46Pitch`, `SeqStep47Pitch`, `SeqStep48Pitch`, `SeqStep49Pitch`, `SeqStep50Pitch`, `SeqStep51Pitch`, `SeqStep52Pitch`, `SeqStep53Pitch`, `SeqStep54Pitch`, `SeqStep55Pitch`, `SeqStep56Pitch`, `SeqStep57Pitch`, `SeqStep58Pitch`, `SeqStep59Pitch`, `SeqStep60Pitch`, `SeqStep61Pitch`, `SeqStep62Pitch`, `SeqStep63Pitch`, `SeqStep64Pitch`

### `SeqStepType*` (32)

`SeqStep33Type`, `SeqStep34Type`, `SeqStep35Type`, `SeqStep36Type`, `SeqStep37Type`, `SeqStep38Type`, `SeqStep39Type`, `SeqStep40Type`, `SeqStep41Type`, `SeqStep42Type`, `SeqStep43Type`, `SeqStep44Type`, `SeqStep45Type`, `SeqStep46Type`, `SeqStep47Type`, `SeqStep48Type`, `SeqStep49Type`, `SeqStep50Type`, `SeqStep51Type`, `SeqStep52Type`, `SeqStep53Type`, `SeqStep54Type`, `SeqStep55Type`, `SeqStep56Type`, `SeqStep57Type`, `SeqStep58Type`, `SeqStep59Type`, `SeqStep60Type`, `SeqStep61Type`, `SeqStep62Type`, `SeqStep63Type`, `SeqStep64Type`

### `SeqStepVelo*` (32)

`SeqStep33Velo`, `SeqStep34Velo`, `SeqStep35Velo`, `SeqStep36Velo`, `SeqStep37Velo`, `SeqStep38Velo`, `SeqStep39Velo`, `SeqStep40Velo`, `SeqStep41Velo`, `SeqStep42Velo`, `SeqStep43Velo`, `SeqStep44Velo`, `SeqStep45Velo`, `SeqStep46Velo`, `SeqStep47Velo`, `SeqStep48Velo`, `SeqStep49Velo`, `SeqStep50Velo`, `SeqStep51Velo`, `SeqStep52Velo`, `SeqStep53Velo`, `SeqStep54Velo`, `SeqStep55Velo`, `SeqStep56Velo`, `SeqStep57Velo`, `SeqStep58Velo`, `SeqStep59Velo`, `SeqStep60Velo`, `SeqStep61Velo`, `SeqStep62Velo`, `SeqStep63Velo`, `SeqStep64Velo`

### `TremoloDepth*` (1)

`TremoloDepth`

### `TremoloPhaseDiff*` (1)

`TremoloPhaseDiff`

### `TremoloShape*` (1)

`TremoloShape`

### `TremoloSmooth*` (1)

`TremoloSmooth`

### `TremoloSpeed*` (1)

`TremoloSpeed`

### `TremoloSync*` (1)

`TremoloSync`

### `TremoloSyncPhase*` (1)

`TremoloSyncPhase`

### `TremoloSyncRatio*` (1)

`TremoloSyncRatio`

### `TuningDenom*` (1)

`TuningDenom`

### `TuningIntFromPrev*` (1)

`TuningIntFromPrev`

### `TuningIntFromRoot*` (1)

`TuningIntFromRoot`

### `TuningMidiPitch*` (1)

`TuningMidiPitch`

### `TuningNum*` (1)

`TuningNum`

### `TuningRepeatType*` (1)

`TuningRepeatType`

### `TuningRootKey*` (1)

`TuningRootKey`

### `TuningStep*` (1)

`TuningStep`

### `TuningStepType*` (1)

`TuningStepType`

### `VMacroDestSelection*` (1)

`V4MacroDestSelection`

### `VMacroSelection*` (1)

`V4MacroSelection`

### `VOscKernelActive*` (18)

`V4Osc1Kernel1Active`, `V4Osc1Kernel2Active`, `V4Osc1Kernel3Active`, `V4Osc1Kernel4Active`, `V4Osc1Kernel5Active`, `V4Osc1Kernel6Active`, `V4Osc2Kernel1Active`, `V4Osc2Kernel2Active`, `V4Osc2Kernel3Active`, `V4Osc2Kernel4Active`, `V4Osc2Kernel5Active`, `V4Osc2Kernel6Active`, `V4Osc3Kernel1Active`, `V4Osc3Kernel2Active`, `V4Osc3Kernel3Active`, `V4Osc3Kernel4Active`, `V4Osc3Kernel5Active`, `V4Osc3Kernel6Active`

### `VOscKernelAttack*` (18)

`V4Osc1Kernel1Attack`, `V4Osc1Kernel2Attack`, `V4Osc1Kernel3Attack`, `V4Osc1Kernel4Attack`, `V4Osc1Kernel5Attack`, `V4Osc1Kernel6Attack`, `V4Osc2Kernel1Attack`, `V4Osc2Kernel2Attack`, `V4Osc2Kernel3Attack`, `V4Osc2Kernel4Attack`, `V4Osc2Kernel5Attack`, `V4Osc2Kernel6Attack`, `V4Osc3Kernel1Attack`, `V4Osc3Kernel2Attack`, `V4Osc3Kernel3Attack`, `V4Osc3Kernel4Attack`, `V4Osc3Kernel5Attack`, `V4Osc3Kernel6Attack`

### `VOscKernelDecay*` (36)

`V4Osc1Kernel1Decay`, `V4Osc1Kernel1Decay2`, `V4Osc1Kernel2Decay`, `V4Osc1Kernel2Decay2`, `V4Osc1Kernel3Decay`, `V4Osc1Kernel3Decay2`, `V4Osc1Kernel4Decay`, `V4Osc1Kernel4Decay2`, `V4Osc1Kernel5Decay`, `V4Osc1Kernel5Decay2`, `V4Osc1Kernel6Decay`, `V4Osc1Kernel6Decay2`, `V4Osc2Kernel1Decay`, `V4Osc2Kernel1Decay2`, `V4Osc2Kernel2Decay`, `V4Osc2Kernel2Decay2`, `V4Osc2Kernel3Decay`, `V4Osc2Kernel3Decay2`, `V4Osc2Kernel4Decay`, `V4Osc2Kernel4Decay2`, `V4Osc2Kernel5Decay`, `V4Osc2Kernel5Decay2`, `V4Osc2Kernel6Decay`, `V4Osc2Kernel6Decay2`, `V4Osc3Kernel1Decay`, `V4Osc3Kernel1Decay2`, `V4Osc3Kernel2Decay`, `V4Osc3Kernel2Decay2`, `V4Osc3Kernel3Decay`, `V4Osc3Kernel3Decay2`, `V4Osc3Kernel4Decay`, `V4Osc3Kernel4Decay2`, `V4Osc3Kernel5Decay`, `V4Osc3Kernel5Decay2`, `V4Osc3Kernel6Decay`, `V4Osc3Kernel6Decay2`

### `VOscKernelDetune*` (18)

`V4Osc1Kernel1Detune`, `V4Osc1Kernel2Detune`, `V4Osc1Kernel3Detune`, `V4Osc1Kernel4Detune`, `V4Osc1Kernel5Detune`, `V4Osc1Kernel6Detune`, `V4Osc2Kernel1Detune`, `V4Osc2Kernel2Detune`, `V4Osc2Kernel3Detune`, `V4Osc2Kernel4Detune`, `V4Osc2Kernel5Detune`, `V4Osc2Kernel6Detune`, `V4Osc3Kernel1Detune`, `V4Osc3Kernel2Detune`, `V4Osc3Kernel3Detune`, `V4Osc3Kernel4Detune`, `V4Osc3Kernel5Detune`, `V4Osc3Kernel6Detune`

### `VOscKernelFeedback*` (18)

`V4Osc1Kernel1Feedback`, `V4Osc1Kernel2Feedback`, `V4Osc1Kernel3Feedback`, `V4Osc1Kernel4Feedback`, `V4Osc1Kernel5Feedback`, `V4Osc1Kernel6Feedback`, `V4Osc2Kernel1Feedback`, `V4Osc2Kernel2Feedback`, `V4Osc2Kernel3Feedback`, `V4Osc2Kernel4Feedback`, `V4Osc2Kernel5Feedback`, `V4Osc2Kernel6Feedback`, `V4Osc3Kernel1Feedback`, `V4Osc3Kernel2Feedback`, `V4Osc3Kernel3Feedback`, `V4Osc3Kernel4Feedback`, `V4Osc3Kernel5Feedback`, `V4Osc3Kernel6Feedback`

### `VOscKernelHighBias*` (18)

`V4Osc1Kernel1HighBias`, `V4Osc1Kernel2HighBias`, `V4Osc1Kernel3HighBias`, `V4Osc1Kernel4HighBias`, `V4Osc1Kernel5HighBias`, `V4Osc1Kernel6HighBias`, `V4Osc2Kernel1HighBias`, `V4Osc2Kernel2HighBias`, `V4Osc2Kernel3HighBias`, `V4Osc2Kernel4HighBias`, `V4Osc2Kernel5HighBias`, `V4Osc2Kernel6HighBias`, `V4Osc3Kernel1HighBias`, `V4Osc3Kernel2HighBias`, `V4Osc3Kernel3HighBias`, `V4Osc3Kernel4HighBias`, `V4Osc3Kernel5HighBias`, `V4Osc3Kernel6HighBias`

### `VOscKernelHighSplit*` (18)

`V4Osc1Kernel1HighSplit`, `V4Osc1Kernel2HighSplit`, `V4Osc1Kernel3HighSplit`, `V4Osc1Kernel4HighSplit`, `V4Osc1Kernel5HighSplit`, `V4Osc1Kernel6HighSplit`, `V4Osc2Kernel1HighSplit`, `V4Osc2Kernel2HighSplit`, `V4Osc2Kernel3HighSplit`, `V4Osc2Kernel4HighSplit`, `V4Osc2Kernel5HighSplit`, `V4Osc2Kernel6HighSplit`, `V4Osc3Kernel1HighSplit`, `V4Osc3Kernel2HighSplit`, `V4Osc3Kernel3HighSplit`, `V4Osc3Kernel4HighSplit`, `V4Osc3Kernel5HighSplit`, `V4Osc3Kernel6HighSplit`

### `VOscKernelLevel*` (36)

`V4Osc1Kernel1Level`, `V4Osc1Kernel1Level1`, `V4Osc1Kernel2Level`, `V4Osc1Kernel2Level1`, `V4Osc1Kernel3Level`, `V4Osc1Kernel3Level1`, `V4Osc1Kernel4Level`, `V4Osc1Kernel4Level1`, `V4Osc1Kernel5Level`, `V4Osc1Kernel5Level1`, `V4Osc1Kernel6Level`, `V4Osc1Kernel6Level1`, `V4Osc2Kernel1Level`, `V4Osc2Kernel1Level1`, `V4Osc2Kernel2Level`, `V4Osc2Kernel2Level1`, `V4Osc2Kernel3Level`, `V4Osc2Kernel3Level1`, `V4Osc2Kernel4Level`, `V4Osc2Kernel4Level1`, `V4Osc2Kernel5Level`, `V4Osc2Kernel5Level1`, `V4Osc2Kernel6Level`, `V4Osc2Kernel6Level1`, `V4Osc3Kernel1Level`, `V4Osc3Kernel1Level1`, `V4Osc3Kernel2Level`, `V4Osc3Kernel2Level1`, `V4Osc3Kernel3Level`, `V4Osc3Kernel3Level1`, `V4Osc3Kernel4Level`, `V4Osc3Kernel4Level1`, `V4Osc3Kernel5Level`, `V4Osc3Kernel5Level1`, `V4Osc3Kernel6Level`, `V4Osc3Kernel6Level1`

### `VOscKernelLevelScale*` (18)

`V4Osc1Kernel1LevelScale`, `V4Osc1Kernel2LevelScale`, `V4Osc1Kernel3LevelScale`, `V4Osc1Kernel4LevelScale`, `V4Osc1Kernel5LevelScale`, `V4Osc1Kernel6LevelScale`, `V4Osc2Kernel1LevelScale`, `V4Osc2Kernel2LevelScale`, `V4Osc2Kernel3LevelScale`, `V4Osc2Kernel4LevelScale`, `V4Osc2Kernel5LevelScale`, `V4Osc2Kernel6LevelScale`, `V4Osc3Kernel1LevelScale`, `V4Osc3Kernel2LevelScale`, `V4Osc3Kernel3LevelScale`, `V4Osc3Kernel4LevelScale`, `V4Osc3Kernel5LevelScale`, `V4Osc3Kernel6LevelScale`

### `VOscKernelLowBias*` (18)

`V4Osc1Kernel1LowBias`, `V4Osc1Kernel2LowBias`, `V4Osc1Kernel3LowBias`, `V4Osc1Kernel4LowBias`, `V4Osc1Kernel5LowBias`, `V4Osc1Kernel6LowBias`, `V4Osc2Kernel1LowBias`, `V4Osc2Kernel2LowBias`, `V4Osc2Kernel3LowBias`, `V4Osc2Kernel4LowBias`, `V4Osc2Kernel5LowBias`, `V4Osc2Kernel6LowBias`, `V4Osc3Kernel1LowBias`, `V4Osc3Kernel2LowBias`, `V4Osc3Kernel3LowBias`, `V4Osc3Kernel4LowBias`, `V4Osc3Kernel5LowBias`, `V4Osc3Kernel6LowBias`

### `VOscKernelLowSplit*` (18)

`V4Osc1Kernel1LowSplit`, `V4Osc1Kernel2LowSplit`, `V4Osc1Kernel3LowSplit`, `V4Osc1Kernel4LowSplit`, `V4Osc1Kernel5LowSplit`, `V4Osc1Kernel6LowSplit`, `V4Osc2Kernel1LowSplit`, `V4Osc2Kernel2LowSplit`, `V4Osc2Kernel3LowSplit`, `V4Osc2Kernel4LowSplit`, `V4Osc2Kernel5LowSplit`, `V4Osc2Kernel6LowSplit`, `V4Osc3Kernel1LowSplit`, `V4Osc3Kernel2LowSplit`, `V4Osc3Kernel3LowSplit`, `V4Osc3Kernel4LowSplit`, `V4Osc3Kernel5LowSplit`, `V4Osc3Kernel6LowSplit`

### `VOscKernelModSrc*` (54)

`V4Osc1Kernel1ModSrc`, `V4Osc1Kernel1ModSrc2`, `V4Osc1Kernel1ModSrc3`, `V4Osc1Kernel2ModSrc`, `V4Osc1Kernel2ModSrc2`, `V4Osc1Kernel2ModSrc3`, `V4Osc1Kernel3ModSrc`, `V4Osc1Kernel3ModSrc2`, `V4Osc1Kernel3ModSrc3`, `V4Osc1Kernel4ModSrc`, `V4Osc1Kernel4ModSrc2`, `V4Osc1Kernel4ModSrc3`, `V4Osc1Kernel5ModSrc`, `V4Osc1Kernel5ModSrc2`, `V4Osc1Kernel5ModSrc3`, `V4Osc1Kernel6ModSrc`, `V4Osc1Kernel6ModSrc2`, `V4Osc1Kernel6ModSrc3`, `V4Osc2Kernel1ModSrc`, `V4Osc2Kernel1ModSrc2`, `V4Osc2Kernel1ModSrc3`, `V4Osc2Kernel2ModSrc`, `V4Osc2Kernel2ModSrc2`, `V4Osc2Kernel2ModSrc3`, `V4Osc2Kernel3ModSrc`, `V4Osc2Kernel3ModSrc2`, `V4Osc2Kernel3ModSrc3`, `V4Osc2Kernel4ModSrc`, `V4Osc2Kernel4ModSrc2`, `V4Osc2Kernel4ModSrc3`, `V4Osc2Kernel5ModSrc`, `V4Osc2Kernel5ModSrc2`, `V4Osc2Kernel5ModSrc3`, `V4Osc2Kernel6ModSrc`, `V4Osc2Kernel6ModSrc2`, `V4Osc2Kernel6ModSrc3`, `V4Osc3Kernel1ModSrc`, `V4Osc3Kernel1ModSrc2`, `V4Osc3Kernel1ModSrc3`, `V4Osc3Kernel2ModSrc`, `V4Osc3Kernel2ModSrc2`, `V4Osc3Kernel2ModSrc3`, `V4Osc3Kernel3ModSrc`, `V4Osc3Kernel3ModSrc2`, `V4Osc3Kernel3ModSrc3`, `V4Osc3Kernel4ModSrc`, `V4Osc3Kernel4ModSrc2`, `V4Osc3Kernel4ModSrc3`, `V4Osc3Kernel5ModSrc`, `V4Osc3Kernel5ModSrc2`, `V4Osc3Kernel5ModSrc3`, `V4Osc3Kernel6ModSrc`, `V4Osc3Kernel6ModSrc2`, `V4Osc3Kernel6ModSrc3`

### `VOscKernelModType*` (18)

`V4Osc1Kernel1ModType`, `V4Osc1Kernel2ModType`, `V4Osc1Kernel3ModType`, `V4Osc1Kernel4ModType`, `V4Osc1Kernel5ModType`, `V4Osc1Kernel6ModType`, `V4Osc2Kernel1ModType`, `V4Osc2Kernel2ModType`, `V4Osc2Kernel3ModType`, `V4Osc2Kernel4ModType`, `V4Osc2Kernel5ModType`, `V4Osc2Kernel6ModType`, `V4Osc3Kernel1ModType`, `V4Osc3Kernel2ModType`, `V4Osc3Kernel3ModType`, `V4Osc3Kernel4ModType`, `V4Osc3Kernel5ModType`, `V4Osc3Kernel6ModType`

### `VOscKernelOutDest*` (18)

`V4Osc1Kernel1OutDest`, `V4Osc1Kernel2OutDest`, `V4Osc1Kernel3OutDest`, `V4Osc1Kernel4OutDest`, `V4Osc1Kernel5OutDest`, `V4Osc1Kernel6OutDest`, `V4Osc2Kernel1OutDest`, `V4Osc2Kernel2OutDest`, `V4Osc2Kernel3OutDest`, `V4Osc2Kernel4OutDest`, `V4Osc2Kernel5OutDest`, `V4Osc2Kernel6OutDest`, `V4Osc3Kernel1OutDest`, `V4Osc3Kernel2OutDest`, `V4Osc3Kernel3OutDest`, `V4Osc3Kernel4OutDest`, `V4Osc3Kernel5OutDest`, `V4Osc3Kernel6OutDest`

### `VOscKernelOutPan*` (18)

`V4Osc1Kernel1OutPan`, `V4Osc1Kernel2OutPan`, `V4Osc1Kernel3OutPan`, `V4Osc1Kernel4OutPan`, `V4Osc1Kernel5OutPan`, `V4Osc1Kernel6OutPan`, `V4Osc2Kernel1OutPan`, `V4Osc2Kernel2OutPan`, `V4Osc2Kernel3OutPan`, `V4Osc2Kernel4OutPan`, `V4Osc2Kernel5OutPan`, `V4Osc2Kernel6OutPan`, `V4Osc3Kernel1OutPan`, `V4Osc3Kernel2OutPan`, `V4Osc3Kernel3OutPan`, `V4Osc3Kernel4OutPan`, `V4Osc3Kernel5OutPan`, `V4Osc3Kernel6OutPan`

### `VOscKernelPhase*` (18)

`V4Osc1Kernel1Phase`, `V4Osc1Kernel2Phase`, `V4Osc1Kernel3Phase`, `V4Osc1Kernel4Phase`, `V4Osc1Kernel5Phase`, `V4Osc1Kernel6Phase`, `V4Osc2Kernel1Phase`, `V4Osc2Kernel2Phase`, `V4Osc2Kernel3Phase`, `V4Osc2Kernel4Phase`, `V4Osc2Kernel5Phase`, `V4Osc2Kernel6Phase`, `V4Osc3Kernel1Phase`, `V4Osc3Kernel2Phase`, `V4Osc3Kernel3Phase`, `V4Osc3Kernel4Phase`, `V4Osc3Kernel5Phase`, `V4Osc3Kernel6Phase`

### `VOscKernelPitchMode*` (18)

`V4Osc1Kernel1PitchMode`, `V4Osc1Kernel2PitchMode`, `V4Osc1Kernel3PitchMode`, `V4Osc1Kernel4PitchMode`, `V4Osc1Kernel5PitchMode`, `V4Osc1Kernel6PitchMode`, `V4Osc2Kernel1PitchMode`, `V4Osc2Kernel2PitchMode`, `V4Osc2Kernel3PitchMode`, `V4Osc2Kernel4PitchMode`, `V4Osc2Kernel5PitchMode`, `V4Osc2Kernel6PitchMode`, `V4Osc3Kernel1PitchMode`, `V4Osc3Kernel2PitchMode`, `V4Osc3Kernel3PitchMode`, `V4Osc3Kernel4PitchMode`, `V4Osc3Kernel5PitchMode`, `V4Osc3Kernel6PitchMode`

### `VOscKernelRatio*` (18)

`V4Osc1Kernel1Ratio`, `V4Osc1Kernel2Ratio`, `V4Osc1Kernel3Ratio`, `V4Osc1Kernel4Ratio`, `V4Osc1Kernel5Ratio`, `V4Osc1Kernel6Ratio`, `V4Osc2Kernel1Ratio`, `V4Osc2Kernel2Ratio`, `V4Osc2Kernel3Ratio`, `V4Osc2Kernel4Ratio`, `V4Osc2Kernel5Ratio`, `V4Osc2Kernel6Ratio`, `V4Osc3Kernel1Ratio`, `V4Osc3Kernel2Ratio`, `V4Osc3Kernel3Ratio`, `V4Osc3Kernel4Ratio`, `V4Osc3Kernel5Ratio`, `V4Osc3Kernel6Ratio`

### `VOscKernelRelease*` (18)

`V4Osc1Kernel1Release`, `V4Osc1Kernel2Release`, `V4Osc1Kernel3Release`, `V4Osc1Kernel4Release`, `V4Osc1Kernel5Release`, `V4Osc1Kernel6Release`, `V4Osc2Kernel1Release`, `V4Osc2Kernel2Release`, `V4Osc2Kernel3Release`, `V4Osc2Kernel4Release`, `V4Osc2Kernel5Release`, `V4Osc2Kernel6Release`, `V4Osc3Kernel1Release`, `V4Osc3Kernel2Release`, `V4Osc3Kernel3Release`, `V4Osc3Kernel4Release`, `V4Osc3Kernel5Release`, `V4Osc3Kernel6Release`

### `VOscKernelSolo*` (18)

`V4Osc1Kernel1Solo`, `V4Osc1Kernel2Solo`, `V4Osc1Kernel3Solo`, `V4Osc1Kernel4Solo`, `V4Osc1Kernel5Solo`, `V4Osc1Kernel6Solo`, `V4Osc2Kernel1Solo`, `V4Osc2Kernel2Solo`, `V4Osc2Kernel3Solo`, `V4Osc2Kernel4Solo`, `V4Osc2Kernel5Solo`, `V4Osc2Kernel6Solo`, `V4Osc3Kernel1Solo`, `V4Osc3Kernel2Solo`, `V4Osc3Kernel3Solo`, `V4Osc3Kernel4Solo`, `V4Osc3Kernel5Solo`, `V4Osc3Kernel6Solo`

### `VOscKernelSustain*` (18)

`V4Osc1Kernel1Sustain`, `V4Osc1Kernel2Sustain`, `V4Osc1Kernel3Sustain`, `V4Osc1Kernel4Sustain`, `V4Osc1Kernel5Sustain`, `V4Osc1Kernel6Sustain`, `V4Osc2Kernel1Sustain`, `V4Osc2Kernel2Sustain`, `V4Osc2Kernel3Sustain`, `V4Osc2Kernel4Sustain`, `V4Osc2Kernel5Sustain`, `V4Osc2Kernel6Sustain`, `V4Osc3Kernel1Sustain`, `V4Osc3Kernel2Sustain`, `V4Osc3Kernel3Sustain`, `V4Osc3Kernel4Sustain`, `V4Osc3Kernel5Sustain`, `V4Osc3Kernel6Sustain`

### `VOscKernelType*` (18)

`V4Osc1Kernel1Type`, `V4Osc1Kernel2Type`, `V4Osc1Kernel3Type`, `V4Osc1Kernel4Type`, `V4Osc1Kernel5Type`, `V4Osc1Kernel6Type`, `V4Osc2Kernel1Type`, `V4Osc2Kernel2Type`, `V4Osc2Kernel3Type`, `V4Osc2Kernel4Type`, `V4Osc2Kernel5Type`, `V4Osc2Kernel6Type`, `V4Osc3Kernel1Type`, `V4Osc3Kernel2Type`, `V4Osc3Kernel3Type`, `V4Osc3Kernel4Type`, `V4Osc3Kernel5Type`, `V4Osc3Kernel6Type`

### `VOscKernelVeloDepth*` (18)

`V4Osc1Kernel1VeloDepth`, `V4Osc1Kernel2VeloDepth`, `V4Osc1Kernel3VeloDepth`, `V4Osc1Kernel4VeloDepth`, `V4Osc1Kernel5VeloDepth`, `V4Osc1Kernel6VeloDepth`, `V4Osc2Kernel1VeloDepth`, `V4Osc2Kernel2VeloDepth`, `V4Osc2Kernel3VeloDepth`, `V4Osc2Kernel4VeloDepth`, `V4Osc2Kernel5VeloDepth`, `V4Osc2Kernel6VeloDepth`, `V4Osc3Kernel1VeloDepth`, `V4Osc3Kernel2VeloDepth`, `V4Osc3Kernel3VeloDepth`, `V4Osc3Kernel4VeloDepth`, `V4Osc3Kernel5VeloDepth`, `V4Osc3Kernel6VeloDepth`

### `VOscKernelWavetable*` (18)

`V4Osc1Kernel1Wavetable`, `V4Osc1Kernel2Wavetable`, `V4Osc1Kernel3Wavetable`, `V4Osc1Kernel4Wavetable`, `V4Osc1Kernel5Wavetable`, `V4Osc1Kernel6Wavetable`, `V4Osc2Kernel1Wavetable`, `V4Osc2Kernel2Wavetable`, `V4Osc2Kernel3Wavetable`, `V4Osc2Kernel4Wavetable`, `V4Osc2Kernel5Wavetable`, `V4Osc2Kernel6Wavetable`, `V4Osc3Kernel1Wavetable`, `V4Osc3Kernel2Wavetable`, `V4Osc3Kernel3Wavetable`, `V4Osc3Kernel4Wavetable`, `V4Osc3Kernel5Wavetable`, `V4Osc3Kernel6Wavetable`

### `VOscKernelWtbPos*` (18)

`V4Osc1Kernel1WtbPos`, `V4Osc1Kernel2WtbPos`, `V4Osc1Kernel3WtbPos`, `V4Osc1Kernel4WtbPos`, `V4Osc1Kernel5WtbPos`, `V4Osc1Kernel6WtbPos`, `V4Osc2Kernel1WtbPos`, `V4Osc2Kernel2WtbPos`, `V4Osc2Kernel3WtbPos`, `V4Osc2Kernel4WtbPos`, `V4Osc2Kernel5WtbPos`, `V4Osc2Kernel6WtbPos`, `V4Osc3Kernel1WtbPos`, `V4Osc3Kernel2WtbPos`, `V4Osc3Kernel3WtbPos`, `V4Osc3Kernel4WtbPos`, `V4Osc3Kernel5WtbPos`, `V4Osc3Kernel6WtbPos`

### `VOscMacro*` (15)

`V4Osc1Macro1`, `V4Osc1Macro2`, `V4Osc1Macro3`, `V4Osc1Macro4`, `V4Osc1Macro5`, `V4Osc2Macro1`, `V4Osc2Macro2`, `V4Osc2Macro3`, `V4Osc2Macro4`, `V4Osc2Macro5`, `V4Osc3Macro1`, `V4Osc3Macro2`, `V4Osc3Macro3`, `V4Osc3Macro4`, `V4Osc3Macro5`

### `VOscMacroAmount*` (90)

`V4Osc1Macro1Amount1`, `V4Osc1Macro1Amount2`, `V4Osc1Macro1Amount3`, `V4Osc1Macro1Amount4`, `V4Osc1Macro1Amount5`, `V4Osc1Macro1Amount6`, `V4Osc1Macro2Amount1`, `V4Osc1Macro2Amount2`, `V4Osc1Macro2Amount3`, `V4Osc1Macro2Amount4`, `V4Osc1Macro2Amount5`, `V4Osc1Macro2Amount6`, `V4Osc1Macro3Amount1`, `V4Osc1Macro3Amount2`, `V4Osc1Macro3Amount3`, `V4Osc1Macro3Amount4`, `V4Osc1Macro3Amount5`, `V4Osc1Macro3Amount6`, `V4Osc1Macro4Amount1`, `V4Osc1Macro4Amount2`, `V4Osc1Macro4Amount3`, `V4Osc1Macro4Amount4`, `V4Osc1Macro4Amount5`, `V4Osc1Macro4Amount6`, `V4Osc1Macro5Amount1`, `V4Osc1Macro5Amount2`, `V4Osc1Macro5Amount3`, `V4Osc1Macro5Amount4`, `V4Osc1Macro5Amount5`, `V4Osc1Macro5Amount6`, `V4Osc2Macro1Amount1`, `V4Osc2Macro1Amount2`, `V4Osc2Macro1Amount3`, `V4Osc2Macro1Amount4`, `V4Osc2Macro1Amount5`, `V4Osc2Macro1Amount6`, `V4Osc2Macro2Amount1`, `V4Osc2Macro2Amount2`, `V4Osc2Macro2Amount3`, `V4Osc2Macro2Amount4`, `V4Osc2Macro2Amount5`, `V4Osc2Macro2Amount6`, `V4Osc2Macro3Amount1`, `V4Osc2Macro3Amount2`, `V4Osc2Macro3Amount3`, `V4Osc2Macro3Amount4`, `V4Osc2Macro3Amount5`, `V4Osc2Macro3Amount6`, `V4Osc2Macro4Amount1`, `V4Osc2Macro4Amount2`, `V4Osc2Macro4Amount3`, `V4Osc2Macro4Amount4`, `V4Osc2Macro4Amount5`, `V4Osc2Macro4Amount6`, `V4Osc2Macro5Amount1`, `V4Osc2Macro5Amount2`, `V4Osc2Macro5Amount3`, `V4Osc2Macro5Amount4`, `V4Osc2Macro5Amount5`, `V4Osc2Macro5Amount6`, `V4Osc3Macro1Amount1`, `V4Osc3Macro1Amount2`, `V4Osc3Macro1Amount3`, `V4Osc3Macro1Amount4`, `V4Osc3Macro1Amount5`, `V4Osc3Macro1Amount6`, `V4Osc3Macro2Amount1`, `V4Osc3Macro2Amount2`, `V4Osc3Macro2Amount3`, `V4Osc3Macro2Amount4`, `V4Osc3Macro2Amount5`, `V4Osc3Macro2Amount6`, `V4Osc3Macro3Amount1`, `V4Osc3Macro3Amount2`, `V4Osc3Macro3Amount3`, `V4Osc3Macro3Amount4`, `V4Osc3Macro3Amount5`, `V4Osc3Macro3Amount6`, `V4Osc3Macro4Amount1`, `V4Osc3Macro4Amount2`, `V4Osc3Macro4Amount3`, `V4Osc3Macro4Amount4`, `V4Osc3Macro4Amount5`, `V4Osc3Macro4Amount6`, `V4Osc3Macro5Amount1`, `V4Osc3Macro5Amount2`, `V4Osc3Macro5Amount3`, `V4Osc3Macro5Amount4`, `V4Osc3Macro5Amount5`, `V4Osc3Macro5Amount6`

### `VOscMacroDest*` (90)

`V4Osc1Macro1Dest1`, `V4Osc1Macro1Dest2`, `V4Osc1Macro1Dest3`, `V4Osc1Macro1Dest4`, `V4Osc1Macro1Dest5`, `V4Osc1Macro1Dest6`, `V4Osc1Macro2Dest1`, `V4Osc1Macro2Dest2`, `V4Osc1Macro2Dest3`, `V4Osc1Macro2Dest4`, `V4Osc1Macro2Dest5`, `V4Osc1Macro2Dest6`, `V4Osc1Macro3Dest1`, `V4Osc1Macro3Dest2`, `V4Osc1Macro3Dest3`, `V4Osc1Macro3Dest4`, `V4Osc1Macro3Dest5`, `V4Osc1Macro3Dest6`, `V4Osc1Macro4Dest1`, `V4Osc1Macro4Dest2`, `V4Osc1Macro4Dest3`, `V4Osc1Macro4Dest4`, `V4Osc1Macro4Dest5`, `V4Osc1Macro4Dest6`, `V4Osc1Macro5Dest1`, `V4Osc1Macro5Dest2`, `V4Osc1Macro5Dest3`, `V4Osc1Macro5Dest4`, `V4Osc1Macro5Dest5`, `V4Osc1Macro5Dest6`, `V4Osc2Macro1Dest1`, `V4Osc2Macro1Dest2`, `V4Osc2Macro1Dest3`, `V4Osc2Macro1Dest4`, `V4Osc2Macro1Dest5`, `V4Osc2Macro1Dest6`, `V4Osc2Macro2Dest1`, `V4Osc2Macro2Dest2`, `V4Osc2Macro2Dest3`, `V4Osc2Macro2Dest4`, `V4Osc2Macro2Dest5`, `V4Osc2Macro2Dest6`, `V4Osc2Macro3Dest1`, `V4Osc2Macro3Dest2`, `V4Osc2Macro3Dest3`, `V4Osc2Macro3Dest4`, `V4Osc2Macro3Dest5`, `V4Osc2Macro3Dest6`, `V4Osc2Macro4Dest1`, `V4Osc2Macro4Dest2`, `V4Osc2Macro4Dest3`, `V4Osc2Macro4Dest4`, `V4Osc2Macro4Dest5`, `V4Osc2Macro4Dest6`, `V4Osc2Macro5Dest1`, `V4Osc2Macro5Dest2`, `V4Osc2Macro5Dest3`, `V4Osc2Macro5Dest4`, `V4Osc2Macro5Dest5`, `V4Osc2Macro5Dest6`, `V4Osc3Macro1Dest1`, `V4Osc3Macro1Dest2`, `V4Osc3Macro1Dest3`, `V4Osc3Macro1Dest4`, `V4Osc3Macro1Dest5`, `V4Osc3Macro1Dest6`, `V4Osc3Macro2Dest1`, `V4Osc3Macro2Dest2`, `V4Osc3Macro2Dest3`, `V4Osc3Macro2Dest4`, `V4Osc3Macro2Dest5`, `V4Osc3Macro2Dest6`, `V4Osc3Macro3Dest1`, `V4Osc3Macro3Dest2`, `V4Osc3Macro3Dest3`, `V4Osc3Macro3Dest4`, `V4Osc3Macro3Dest5`, `V4Osc3Macro3Dest6`, `V4Osc3Macro4Dest1`, `V4Osc3Macro4Dest2`, `V4Osc3Macro4Dest3`, `V4Osc3Macro4Dest4`, `V4Osc3Macro4Dest5`, `V4Osc3Macro4Dest6`, `V4Osc3Macro5Dest1`, `V4Osc3Macro5Dest2`, `V4Osc3Macro5Dest3`, `V4Osc3Macro5Dest4`, `V4Osc3Macro5Dest5`, `V4Osc3Macro5Dest6`

### `VOscMacroName*` (15)

`V4Osc1Macro1Name`, `V4Osc1Macro2Name`, `V4Osc1Macro3Name`, `V4Osc1Macro4Name`, `V4Osc1Macro5Name`, `V4Osc2Macro1Name`, `V4Osc2Macro2Name`, `V4Osc2Macro3Name`, `V4Osc2Macro4Name`, `V4Osc2Macro5Name`, `V4Osc3Macro1Name`, `V4Osc3Macro2Name`, `V4Osc3Macro3Name`, `V4Osc3Macro4Name`, `V4Osc3Macro5Name`

### `VOscTemplateName*` (3)

`V4Osc1TemplateName`, `V4Osc2TemplateName`, `V4Osc3TemplateName`

### `VoiceAllocationMode*` (1)

`VoiceAllocationMode`

