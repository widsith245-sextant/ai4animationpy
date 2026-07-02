#include "AI4AnimationNNESubsystem.h"

#include "AI4AnimationNNEModule.h"
#include "AI4AnimationNNEProjectSettings.h"
#include "Dom/JsonObject.h"
#include "HAL/PlatformFileManager.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "NNE.h"
#include "NNEModelData.h"
#include "NNERuntimeCPU.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
	bool TryGetObject(const TSharedPtr<FJsonObject>& Root, const FString& FieldName, TSharedPtr<FJsonObject>& OutObject)
	{
		if (!Root.IsValid())
		{
			return false;
		}

		const TSharedPtr<FJsonObject>* FoundObject = nullptr;
		if (!Root->TryGetObjectField(FieldName, FoundObject) || FoundObject == nullptr)
		{
			return false;
		}

		OutObject = *FoundObject;
		return OutObject.IsValid();
	}

	void ReadStringArray(const TSharedPtr<FJsonObject>& Root, const FString& FieldName, TArray<FString>& OutValues)
	{
		OutValues.Reset();
		if (!Root.IsValid())
		{
			return;
		}

		const TArray<TSharedPtr<FJsonValue>>* JsonValues = nullptr;
		if (!Root->TryGetArrayField(FieldName, JsonValues) || JsonValues == nullptr)
		{
			return;
		}

		for (const TSharedPtr<FJsonValue>& JsonValue : *JsonValues)
		{
			FString TextValue;
			if (JsonValue.IsValid() && JsonValue->TryGetString(TextValue))
			{
				OutValues.Add(TextValue);
			}
		}
	}

	void ReadIntArray(const TSharedPtr<FJsonObject>& Root, const FString& FieldName, TArray<int32>& OutValues)
	{
		OutValues.Reset();
		if (!Root.IsValid())
		{
			return;
		}

		const TArray<TSharedPtr<FJsonValue>>* JsonValues = nullptr;
		if (!Root->TryGetArrayField(FieldName, JsonValues) || JsonValues == nullptr)
		{
			return;
		}

		for (const TSharedPtr<FJsonValue>& JsonValue : *JsonValues)
		{
			if (!JsonValue.IsValid())
			{
				continue;
			}

			const double Number = JsonValue->AsNumber();
			OutValues.Add(static_cast<int32>(Number));
		}
	}

	void ReadStringMap(const TSharedPtr<FJsonObject>& Root, TMap<FString, FString>& OutValues)
	{
		OutValues.Reset();
		if (!Root.IsValid())
		{
			return;
		}

		for (const TPair<FString, TSharedPtr<FJsonValue>>& Entry : Root->Values)
		{
			if (!Entry.Value.IsValid())
			{
				continue;
			}

			FString StringValue;
			switch (Entry.Value->Type)
			{
			case EJson::String:
				StringValue = Entry.Value->AsString();
				break;
			case EJson::Number:
				StringValue = FString::SanitizeFloat(Entry.Value->AsNumber());
				break;
			case EJson::Boolean:
				StringValue = Entry.Value->AsBool() ? TEXT("true") : TEXT("false");
				break;
			default:
				continue;
			}

			OutValues.Add(Entry.Key, StringValue);
		}
	}
}

void UAI4AnimationNNESubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	const UAI4AnimationNNEProjectSettings* Settings = GetDefault<UAI4AnimationNNEProjectSettings>();
	if (Settings != nullptr && Settings->bLoadDefaultPackageOnInitialize && !Settings->DefaultPackageName.IsEmpty())
	{
		LoadDefaultPackage();
	}
}

void UAI4AnimationNNESubsystem::Deinitialize()
{
	ResetRuntimeState();
	Super::Deinitialize();
}

bool UAI4AnimationNNESubsystem::LoadDefaultPackage()
{
	const UAI4AnimationNNEProjectSettings* Settings = GetDefault<UAI4AnimationNNEProjectSettings>();
	if (Settings == nullptr || Settings->DefaultPackageName.IsEmpty())
	{
		LastError = TEXT("Default package name is empty in AI4Animation NNE project settings.");
		return false;
	}

	return LoadPackageByName(Settings->DefaultPackageName);
}

bool UAI4AnimationNNESubsystem::LoadPackageByName(const FString& PackageName)
{
	const FString PackageRoot = ResolveModelPackageRoot();
	const FString ManifestPath = FPaths::Combine(PackageRoot, PackageName, PackageName + TEXT(".ue.json"));
	return LoadPackageFromManifest(ManifestPath);
}

bool UAI4AnimationNNESubsystem::LoadPackageFromManifest(const FString& ManifestPath)
{
	FAI4AnimationNNEModelPackage ParsedPackage;
	FString ParseError;
	if (!ParseManifest(ManifestPath, ParsedPackage, ParseError))
	{
		LastError = ParseError;
		UE_LOG(LogAI4AnimationNNE, Error, TEXT("%s"), *LastError);
		return false;
	}

	FString RuntimeError;
	if (!CreateModelInstanceFromPackage(ParsedPackage, RuntimeError))
	{
		LastError = RuntimeError;
		UE_LOG(LogAI4AnimationNNE, Error, TEXT("%s"), *LastError);
		return false;
	}

	ActivePackage = ParsedPackage;
	LastError.Reset();
	UE_LOG(LogAI4AnimationNNE, Log, TEXT("Loaded AI4Animation package '%s' from '%s'."), *ActivePackage.PackageName, *ActivePackage.ManifestPath);
	return true;
}

bool UAI4AnimationNNESubsystem::RunInference(const TArray<float>& Input, TArray<float>& Output)
{
	if (!ModelInstance.IsValid())
	{
		LastError = TEXT("No NNE model instance is loaded.");
		return false;
	}

	if (Input.Num() == 0)
	{
		LastError = TEXT("Input tensor is empty.");
		return false;
	}

	const TConstArrayView<UE::NNE::FTensorDesc> InputDescs = ModelInstance->GetInputTensorDescs();
	const TConstArrayView<UE::NNE::FTensorDesc> OutputDescs = ModelInstance->GetOutputTensorDescs();
	if (InputDescs.Num() != 1 || OutputDescs.Num() != 1)
	{
		LastError = TEXT("Only single-input single-output models are currently supported.");
		return false;
	}

	const UE::NNE::FTensorShape InputShape = UE::NNE::FTensorShape::Make({1u, static_cast<uint32>(Input.Num())});
	if (ModelInstance->SetInputTensorShapes({InputShape}) != UE::NNE::EResultStatus::Ok)
	{
		LastError = TEXT("Failed to set model input tensor shape.");
		return false;
	}

	const TConstArrayView<UE::NNE::FTensorShape> OutputShapes = ModelInstance->GetOutputTensorShapes();
	if (OutputShapes.Num() != 1)
	{
		LastError = TEXT("Model did not resolve a single concrete output tensor shape.");
		return false;
	}

	const uint64 OutputTensorSizeInBytes = OutputDescs[0].GetElementByteSize() * OutputShapes[0].Volume();
	if (OutputTensorSizeInBytes == 0 || OutputDescs[0].GetElementByteSize() != sizeof(float))
	{
		LastError = TEXT("Only float output tensors are currently supported.");
		return false;
	}

	Output.SetNumUninitialized(static_cast<int32>(OutputTensorSizeInBytes / sizeof(float)));

	UE::NNE::FTensorBindingCPU InputBinding;
	InputBinding.Data = const_cast<float*>(Input.GetData());
	InputBinding.SizeInBytes = static_cast<uint64>(Input.Num()) * sizeof(float);

	UE::NNE::FTensorBindingCPU OutputBinding;
	OutputBinding.Data = Output.GetData();
	OutputBinding.SizeInBytes = OutputTensorSizeInBytes;

	if (ModelInstance->RunSync({InputBinding}, {OutputBinding}) != UE::NNE::EResultStatus::Ok)
	{
		LastError = TEXT("NNE synchronous inference failed.");
		return false;
	}

	LastError.Reset();
	return true;
}

bool UAI4AnimationNNESubsystem::IsModelLoaded() const
{
	return ModelInstance.IsValid() && ActivePackage.IsValid();
}

const FAI4AnimationNNEModelPackage& UAI4AnimationNNESubsystem::GetActivePackage() const
{
	return ActivePackage;
}

FString UAI4AnimationNNESubsystem::GetLastError() const
{
	return LastError;
}

int32 UAI4AnimationNNESubsystem::GetExpectedInputElementCount() const
{
	if (ActivePackage.ModelIO.InputShape.Num() > 0)
	{
		int32 Product = 1;
		for (const int32 Dimension : ActivePackage.ModelIO.InputShape)
		{
			if (Dimension > 0)
			{
				Product *= Dimension;
			}
		}
		return Product;
	}

	return 0;
}

bool UAI4AnimationNNESubsystem::ParseManifest(const FString& ManifestPath, FAI4AnimationNNEModelPackage& OutManifest, FString& OutError) const
{
	FString JsonText;
	if (!FFileHelper::LoadFileToString(JsonText, *ManifestPath))
	{
		OutError = FString::Printf(TEXT("Failed to read AI4Animation manifest: %s"), *ManifestPath);
		return false;
	}

	TSharedPtr<FJsonObject> RootObject;
	TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
	if (!FJsonSerializer::Deserialize(Reader, RootObject) || !RootObject.IsValid())
	{
		OutError = FString::Printf(TEXT("Failed to parse JSON manifest: %s"), *ManifestPath);
		return false;
	}

	OutManifest = FAI4AnimationNNEModelPackage();
	OutManifest.ManifestPath = FPaths::ConvertRelativePathToFull(ManifestPath);
	RootObject->TryGetStringField(TEXT("schema_version"), OutManifest.SchemaVersion);
	RootObject->TryGetStringField(TEXT("package_name"), OutManifest.PackageName);
	RootObject->TryGetStringField(TEXT("source_checkpoint"), OutManifest.SourceCheckpoint);

	double SampleRate = 0.0;
	if (RootObject->TryGetNumberField(TEXT("sample_rate"), SampleRate))
	{
		OutManifest.SampleRate = static_cast<int32>(SampleRate);
	}

	ReadStringArray(RootObject, TEXT("compatible_input_formats"), OutManifest.CompatibleInputFormats);

	TSharedPtr<FJsonObject> RuntimeObject;
	if (TryGetObject(RootObject, TEXT("runtime"), RuntimeObject))
	{
		RuntimeObject->TryGetStringField(TEXT("preferred_name"), OutManifest.RuntimeName);
	}

	TSharedPtr<FJsonObject> OnnxObject;
	if (TryGetObject(RootObject, TEXT("onnx"), OnnxObject))
	{
		OnnxObject->TryGetStringField(TEXT("path"), OutManifest.OnnxPath);
	}

	TSharedPtr<FJsonObject> SkeletonObject;
	if (TryGetObject(RootObject, TEXT("skeleton"), SkeletonObject))
	{
		ReadStringArray(SkeletonObject, TEXT("bone_names"), OutManifest.BoneNames);
	}

	TSharedPtr<FJsonObject> ModelIOObject;
	if (TryGetObject(RootObject, TEXT("model_io"), ModelIOObject))
	{
		ModelIOObject->TryGetStringField(TEXT("input_name"), OutManifest.ModelIO.InputName);
		ModelIOObject->TryGetStringField(TEXT("output_name"), OutManifest.ModelIO.OutputName);
		ReadIntArray(ModelIOObject, TEXT("input_shape"), OutManifest.ModelIO.InputShape);

		double OpsetVersion = 0.0;
		if (ModelIOObject->TryGetNumberField(TEXT("opset_version"), OpsetVersion))
		{
			OutManifest.ModelIO.OpsetVersion = static_cast<int32>(OpsetVersion);
		}

		bool bDynamicBatch = true;
		if (ModelIOObject->TryGetBoolField(TEXT("dynamic_batch"), bDynamicBatch))
		{
			OutManifest.ModelIO.bDynamicBatch = bDynamicBatch;
		}
	}

	TSharedPtr<FJsonObject> RetargetingObject;
	if (TryGetObject(RootObject, TEXT("retargeting"), RetargetingObject))
	{
		RetargetingObject->TryGetStringField(TEXT("primary_ue_skeleton"), OutManifest.Retargeting.PrimaryUESkeleton);
		RetargetingObject->TryGetStringField(TEXT("strategy"), OutManifest.Retargeting.Strategy);
		bool bSupportsCustomSkeletons = true;
		if (RetargetingObject->TryGetBoolField(TEXT("supports_custom_skeletons"), bSupportsCustomSkeletons))
		{
			OutManifest.Retargeting.bSupportsCustomSkeletons = bSupportsCustomSkeletons;
		}
	}

	TSharedPtr<FJsonObject> TerrainObject;
	if (TryGetObject(RootObject, TEXT("terrain"), TerrainObject))
	{
		bool bSlope = true;
		bool bHeight = true;
		TerrainObject->TryGetBoolField(TEXT("supports_variable_slope"), bSlope);
		TerrainObject->TryGetBoolField(TEXT("supports_height_variation"), bHeight);
		TerrainObject->TryGetStringField(TEXT("training_expectation"), OutManifest.Terrain.TrainingExpectation);
		OutManifest.Terrain.bSupportsVariableSlope = bSlope;
		OutManifest.Terrain.bSupportsHeightVariation = bHeight;
	}

	TSharedPtr<FJsonObject> ExtraObject;
	if (TryGetObject(RootObject, TEXT("extra_metadata"), ExtraObject))
	{
		ReadStringMap(ExtraObject, OutManifest.ExtraMetadata);
	}

	if (OutManifest.PackageName.IsEmpty())
	{
		OutError = FString::Printf(TEXT("Manifest '%s' is missing package_name."), *ManifestPath);
		return false;
	}

	if (OutManifest.OnnxPath.IsEmpty())
	{
		OutError = FString::Printf(TEXT("Manifest '%s' is missing onnx.path."), *ManifestPath);
		return false;
	}

	if (FPaths::IsRelative(OutManifest.OnnxPath))
	{
		OutManifest.OnnxPath = FPaths::ConvertRelativePathToFull(FPaths::GetPath(OutManifest.ManifestPath), OutManifest.OnnxPath);
	}

	return true;
}

bool UAI4AnimationNNESubsystem::CreateModelInstanceFromPackage(const FAI4AnimationNNEModelPackage& InPackage, FString& OutError)
{
	ResetRuntimeState();

	TArray64<uint8> OnnxBytes;
	if (!FFileHelper::LoadFileToArray(OnnxBytes, *InPackage.OnnxPath))
	{
		OutError = FString::Printf(TEXT("Failed to read ONNX file: %s"), *InPackage.OnnxPath);
		return false;
	}

	RuntimeModelData = NewObject<UNNEModelData>(this);
	RuntimeModelData->Init(TEXT("onnx"), OnnxBytes);

	const UAI4AnimationNNEProjectSettings* Settings = GetDefault<UAI4AnimationNNEProjectSettings>();
	const FString RuntimeName = !InPackage.RuntimeName.IsEmpty()
		? InPackage.RuntimeName
		: (Settings != nullptr ? Settings->DefaultRuntimeName : TEXT("NNERuntimeORTCpu"));

	TWeakInterfacePtr<INNERuntimeCPU> Runtime = UE::NNE::GetRuntime<INNERuntimeCPU>(RuntimeName);
	if (!Runtime.IsValid())
	{
		OutError = FString::Printf(TEXT("NNE runtime '%s' is not available."), *RuntimeName);
		return false;
	}

	if (Runtime->CanCreateModelCPU(RuntimeModelData) != UE::NNE::EResultStatus::Ok)
	{
		OutError = FString::Printf(TEXT("Runtime '%s' cannot create a CPU model from '%s'."), *RuntimeName, *InPackage.OnnxPath);
		return false;
	}

	Model = Runtime->CreateModelCPU(RuntimeModelData);
	if (!Model.IsValid())
	{
		OutError = FString::Printf(TEXT("Runtime '%s' failed to create the model."), *RuntimeName);
		return false;
	}

	ModelInstance = Model->CreateModelInstanceCPU();
	if (!ModelInstance.IsValid())
	{
		OutError = FString::Printf(TEXT("Runtime '%s' failed to create the model instance."), *RuntimeName);
		return false;
	}

	return true;
}

FString UAI4AnimationNNESubsystem::ResolveModelPackageRoot() const
{
	const UAI4AnimationNNEProjectSettings* Settings = GetDefault<UAI4AnimationNNEProjectSettings>();
	if (Settings == nullptr)
	{
		return FPaths::ProjectPluginsDir();
	}

	if (Settings->bPreferPluginResourceDirectory)
	{
		const TSharedPtr<IPlugin> Plugin = IPluginManager::Get().FindPlugin(TEXT("AI4AnimationNNE"));
		if (Plugin.IsValid())
		{
			return FPaths::Combine(Plugin->GetBaseDir(), Settings->RelativeModelPackageRoot);
		}
	}

	if (FPaths::IsRelative(Settings->RelativeModelPackageRoot))
	{
		return FPaths::ConvertRelativePathToFull(FPaths::ProjectDir(), Settings->RelativeModelPackageRoot);
	}

	return Settings->RelativeModelPackageRoot;
}

void UAI4AnimationNNESubsystem::ResetRuntimeState()
{
	ModelInstance.Reset();
	Model.Reset();
	RuntimeModelData = nullptr;
	ActivePackage = FAI4AnimationNNEModelPackage();
}
