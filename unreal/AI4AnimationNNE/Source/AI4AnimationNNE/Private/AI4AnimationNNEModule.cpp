#include "AI4AnimationNNEModule.h"

DEFINE_LOG_CATEGORY(LogAI4AnimationNNE);

void FAI4AnimationNNEModule::StartupModule()
{
	UE_LOG(LogAI4AnimationNNE, Log, TEXT("AI4AnimationNNE module started."));
}

void FAI4AnimationNNEModule::ShutdownModule()
{
	UE_LOG(LogAI4AnimationNNE, Log, TEXT("AI4AnimationNNE module shut down."));
}

IMPLEMENT_MODULE(FAI4AnimationNNEModule, AI4AnimationNNE)
