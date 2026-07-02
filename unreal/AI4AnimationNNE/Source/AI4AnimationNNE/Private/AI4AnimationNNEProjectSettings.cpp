#include "AI4AnimationNNEProjectSettings.h"

UAI4AnimationNNEProjectSettings::UAI4AnimationNNEProjectSettings()
{
	CategoryName = TEXT("Plugins");
	SectionName = TEXT("AI4AnimationNNE");
}

FName UAI4AnimationNNEProjectSettings::GetCategoryName() const
{
	return TEXT("Plugins");
}
