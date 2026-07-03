using UnrealBuildTool;

public class AI4AnimationNNEEditor : ModuleRules
{
	public AI4AnimationNNEEditor(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"UnrealEd",
				"AI4AnimationNNE"
			}
		);

		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"AnimationDataController",
				"AssetTools",
				"EditorFramework",
				"Json",
				"JsonUtilities"
			}
		);
	}
}
