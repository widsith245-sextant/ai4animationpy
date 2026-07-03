#include "AI4AnimationNNEEditorLibrary.h"

#include "Animation/AnimData/IAnimationDataController.h"
#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "AssetToolsModule.h"
#include "Factories/AnimSequenceFactory.h"
#include "Engine/SkeletalMesh.h"
#include "JsonObjectConverter.h"
#include "Math/Quat.h"
#include "Math/TransformNonVectorized.h"
#include "Misc/FileHelper.h"
#include "Misc/PackageName.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
	struct FAI4AnimationSourceTrack
	{
		TArray<FVector> Positions;
		TArray<FQuat> Rotations;
	};

	struct FAI4AnimationImportPayload
	{
		float FrameRate = 30.0f;
		int32 NumFrames = 0;
		float RootTranslationScale = 1.0f;
		bool bRebaseRootTranslation = true;
		bool bUseSourceWorldPositionsForAllBones = false;
		bool bSourceRotationsAreLocal = false;
		FString RootSourceBone;
		TMap<FString, FString> BoneMapping;
		TMap<FString, FAI4AnimationSourceTrack> SourceTracks;
	};

	bool ParseVec3Array(const TArray<TSharedPtr<FJsonValue>>& JsonArray, TArray<FVector>& OutValues)
	{
		OutValues.Reserve(JsonArray.Num());
		for (const TSharedPtr<FJsonValue>& Entry : JsonArray)
		{
			const TArray<TSharedPtr<FJsonValue>>* Triple = nullptr;
			if (!Entry.IsValid() || !Entry->TryGetArray(Triple) || Triple->Num() != 3)
			{
				return false;
			}

			OutValues.Emplace(
				static_cast<float>((*Triple)[0]->AsNumber()),
				static_cast<float>((*Triple)[1]->AsNumber()),
				static_cast<float>((*Triple)[2]->AsNumber()));
		}
		return true;
	}

	bool ParseQuatArray(const TArray<TSharedPtr<FJsonValue>>& JsonArray, TArray<FQuat>& OutValues)
	{
		OutValues.Reserve(JsonArray.Num());
		for (const TSharedPtr<FJsonValue>& Entry : JsonArray)
		{
			const TArray<TSharedPtr<FJsonValue>>* Quad = nullptr;
			if (!Entry.IsValid() || !Entry->TryGetArray(Quad) || Quad->Num() != 4)
			{
				return false;
			}

			FQuat Rotation(
				static_cast<float>((*Quad)[0]->AsNumber()),
				static_cast<float>((*Quad)[1]->AsNumber()),
				static_cast<float>((*Quad)[2]->AsNumber()),
				static_cast<float>((*Quad)[3]->AsNumber()));
			Rotation.Normalize();
			OutValues.Add(Rotation);
		}
		return true;
	}

	bool LoadPayload(const FString& JsonPath, FAI4AnimationImportPayload& OutPayload, FString& OutError)
	{
		FString JsonText;
		if (!FFileHelper::LoadFileToString(JsonText, *JsonPath))
		{
			OutError = FString::Printf(TEXT("Could not read JSON file: %s"), *JsonPath);
			return false;
		}

		TSharedPtr<FJsonObject> RootObject;
		const TSharedRef<TJsonReader<>> Reader = TJsonReaderFactory<>::Create(JsonText);
		if (!FJsonSerializer::Deserialize(Reader, RootObject) || !RootObject.IsValid())
		{
			OutError = FString::Printf(TEXT("Could not parse JSON file: %s"), *JsonPath);
			return false;
		}

		OutPayload.FrameRate = static_cast<float>(RootObject->GetNumberField(TEXT("frame_rate")));
		OutPayload.NumFrames = RootObject->GetIntegerField(TEXT("num_frames"));

		const TSharedPtr<FJsonObject>* OptionsObject = nullptr;
		if (RootObject->TryGetObjectField(TEXT("options"), OptionsObject) && OptionsObject && OptionsObject->IsValid())
		{
			OutPayload.RootTranslationScale = static_cast<float>((*OptionsObject)->GetNumberField(TEXT("root_translation_scale")));
			OutPayload.bRebaseRootTranslation = (*OptionsObject)->GetBoolField(TEXT("rebase_root_translation_to_first_frame"));
			OutPayload.RootSourceBone = (*OptionsObject)->GetStringField(TEXT("root_source_bone"));
			(*OptionsObject)->TryGetBoolField(TEXT("use_source_world_positions_for_all_bones"), OutPayload.bUseSourceWorldPositionsForAllBones);
			(*OptionsObject)->TryGetBoolField(TEXT("source_rotations_are_local"), OutPayload.bSourceRotationsAreLocal);
		}

		const TSharedPtr<FJsonObject>* MappingObject = nullptr;
		if (!RootObject->TryGetObjectField(TEXT("bone_mapping"), MappingObject) || !MappingObject || !MappingObject->IsValid())
		{
			OutError = TEXT("Missing bone_mapping in JSON payload.");
			return false;
		}
		for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : (*MappingObject)->Values)
		{
			OutPayload.BoneMapping.Add(Pair.Key, Pair.Value->AsString());
		}

		const TSharedPtr<FJsonObject>* TracksObject = nullptr;
		if (!RootObject->TryGetObjectField(TEXT("source_tracks"), TracksObject) || !TracksObject || !TracksObject->IsValid())
		{
			OutError = TEXT("Missing source_tracks in JSON payload.");
			return false;
		}

		for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : (*TracksObject)->Values)
		{
			const TSharedPtr<FJsonObject>* TrackObject = nullptr;
			if (!Pair.Value.IsValid() || !Pair.Value->TryGetObject(TrackObject) || !TrackObject || !TrackObject->IsValid())
			{
				OutError = FString::Printf(TEXT("Invalid source track object for bone %s."), *Pair.Key);
				return false;
			}

			const TArray<TSharedPtr<FJsonValue>>* PositionsArray = nullptr;
			const TArray<TSharedPtr<FJsonValue>>* RotationsArray = nullptr;
			if (!(*TrackObject)->TryGetArrayField(TEXT("positions"), PositionsArray) ||
				!(*TrackObject)->TryGetArrayField(TEXT("rotations"), RotationsArray))
			{
				OutError = FString::Printf(TEXT("Track %s is missing positions or rotations."), *Pair.Key);
				return false;
			}

			FAI4AnimationSourceTrack Track;
			if (!ParseVec3Array(*PositionsArray, Track.Positions) || !ParseQuatArray(*RotationsArray, Track.Rotations))
			{
				OutError = FString::Printf(TEXT("Track %s contains invalid vector or quaternion data."), *Pair.Key);
				return false;
			}

			if (Track.Positions.Num() != OutPayload.NumFrames || Track.Rotations.Num() != OutPayload.NumFrames)
			{
				OutError = FString::Printf(TEXT("Track %s frame count does not match payload num_frames."), *Pair.Key);
				return false;
			}

			OutPayload.SourceTracks.Add(Pair.Key, MoveTemp(Track));
		}

		return true;
	}
}

bool UAI4AnimationNNEEditorLibrary::ImportClipFromJson(
	const FString& JsonPath,
	const FString& DestinationPackagePath,
	const FString& AssetName,
	const FString& SkeletonAssetPath,
	const FString& PreviewMeshAssetPath,
	FString& OutAssetPath,
	FString& OutErrorMessage)
{
	OutAssetPath.Reset();
	OutErrorMessage.Reset();

	FAI4AnimationImportPayload Payload;
	if (!LoadPayload(JsonPath, Payload, OutErrorMessage))
	{
		return false;
	}

	USkeleton* Skeleton = LoadObject<USkeleton>(nullptr, *SkeletonAssetPath);
	if (!Skeleton)
	{
		OutErrorMessage = FString::Printf(TEXT("Failed to load skeleton: %s"), *SkeletonAssetPath);
		return false;
	}

	USkeletalMesh* PreviewMesh = LoadObject<USkeletalMesh>(nullptr, *PreviewMeshAssetPath);
	if (!PreviewMesh)
	{
		OutErrorMessage = FString::Printf(TEXT("Failed to load preview mesh: %s"), *PreviewMeshAssetPath);
		return false;
	}

	const FString PackagePath = DestinationPackagePath.StartsWith(TEXT("/")) ? DestinationPackagePath : FString::Printf(TEXT("/Game/%s"), *DestinationPackagePath);
	UAnimSequenceFactory* Factory = NewObject<UAnimSequenceFactory>();
	Factory->TargetSkeleton = Skeleton;
	Factory->PreviewSkeletalMesh = PreviewMesh;

	FAssetToolsModule& AssetToolsModule = FModuleManager::LoadModuleChecked<FAssetToolsModule>(TEXT("AssetTools"));
	UObject* CreatedAsset = AssetToolsModule.Get().CreateAsset(AssetName, PackagePath, UAnimSequence::StaticClass(), Factory);
	UAnimSequence* AnimSequence = Cast<UAnimSequence>(CreatedAsset);
	if (!AnimSequence)
	{
		OutErrorMessage = TEXT("Failed to create AnimSequence asset.");
		return false;
	}

	const FReferenceSkeleton& RefSkeleton = Skeleton->GetReferenceSkeleton();
	const TArray<FTransform>& RefPose = RefSkeleton.GetRefBonePose();
	const int32 BoneCount = RefSkeleton.GetNum();
	const int32 NumKeys = Payload.NumFrames;
	FName RootTargetBoneName(*Payload.RootSourceBone);
	for (const TPair<FString, FString>& Pair : Payload.BoneMapping)
	{
		if (Pair.Value == Payload.RootSourceBone)
		{
			RootTargetBoneName = FName(*Pair.Key);
			break;
		}
	}

	TMap<FName, TArray<FVector3f>> PositionKeys;
	TMap<FName, TArray<FQuat4f>> RotationKeys;
	TMap<FName, TArray<FVector3f>> ScaleKeys;

	const FAI4AnimationSourceTrack* RootTrack = Payload.SourceTracks.Find(Payload.RootSourceBone);
	FVector RootStart = FVector::ZeroVector;
	if (RootTrack && RootTrack->Positions.Num() > 0)
	{
		RootStart = RootTrack->Positions[0];
	}

	for (const TPair<FString, FString>& Pair : Payload.BoneMapping)
	{
		const FName TargetBoneName(*Pair.Key);
		if (RefSkeleton.FindBoneIndex(TargetBoneName) == INDEX_NONE)
		{
			continue;
		}

		PositionKeys.Add(TargetBoneName, TArray<FVector3f>());
		RotationKeys.Add(TargetBoneName, TArray<FQuat4f>());
		ScaleKeys.Add(TargetBoneName, TArray<FVector3f>());
		PositionKeys[TargetBoneName].Reserve(NumKeys);
		RotationKeys[TargetBoneName].Reserve(NumKeys);
		ScaleKeys[TargetBoneName].Reserve(NumKeys);
	}

	for (int32 FrameIndex = 0; FrameIndex < NumKeys; ++FrameIndex)
	{
		TArray<FTransform> WorldPose;
		WorldPose.SetNum(BoneCount);

		for (int32 BoneIndex = 0; BoneIndex < BoneCount; ++BoneIndex)
		{
			const FName BoneName = RefSkeleton.GetBoneName(BoneIndex);
			const FString* SourceBoneName = Payload.BoneMapping.Find(BoneName.ToString());
			const FAI4AnimationSourceTrack* SourceTrack = SourceBoneName ? Payload.SourceTracks.Find(*SourceBoneName) : nullptr;

			FVector LocalPosition = RefPose[BoneIndex].GetTranslation();
			FQuat LocalRotation = RefPose[BoneIndex].GetRotation();
			LocalRotation.Normalize();

			const int32 ParentIndex = RefSkeleton.GetParentIndex(BoneIndex);
			const FQuat ParentWorldRotation = ParentIndex != INDEX_NONE ? WorldPose[ParentIndex].GetRotation() : FQuat::Identity;

			if (SourceTrack)
			{
				if (Payload.bSourceRotationsAreLocal)
				{
					LocalRotation = SourceTrack->Rotations[FrameIndex];
					LocalRotation.Normalize();
				}
				else
				{
					const FQuat DesiredWorldRotation = SourceTrack->Rotations[FrameIndex];
					LocalRotation = ParentWorldRotation.Inverse() * DesiredWorldRotation;
					LocalRotation.Normalize();
				}

				if (Payload.bUseSourceWorldPositionsForAllBones)
				{
					FVector DesiredWorldPosition = SourceTrack->Positions[FrameIndex];
					if (Payload.bRebaseRootTranslation)
					{
						DesiredWorldPosition -= RootStart;
					}

					DesiredWorldPosition *= Payload.RootTranslationScale;

					if (ParentIndex != INDEX_NONE)
					{
						LocalPosition = WorldPose[ParentIndex].InverseTransformPositionNoScale(DesiredWorldPosition);
					}
					else
					{
						LocalPosition = DesiredWorldPosition;
					}
				}
				else if (BoneName == RootTargetBoneName && RootTrack)
				{
					FVector RootPosition = RootTrack->Positions[FrameIndex];
					if (Payload.bRebaseRootTranslation)
					{
						RootPosition -= RootStart;
					}
					LocalPosition = RootPosition * Payload.RootTranslationScale;
				}
			}

			FTransform LocalTransform(LocalRotation, LocalPosition, RefPose[BoneIndex].GetScale3D());
			if (ParentIndex != INDEX_NONE)
			{
				WorldPose[BoneIndex] = LocalTransform * WorldPose[ParentIndex];
			}
			else
			{
				WorldPose[BoneIndex] = LocalTransform;
			}

			if (PositionKeys.Contains(BoneName))
			{
				PositionKeys[BoneName].Add(FVector3f(LocalPosition));
				RotationKeys[BoneName].Add(FQuat4f(LocalRotation));
				ScaleKeys[BoneName].Add(FVector3f(RefPose[BoneIndex].GetScale3D()));
			}
		}
	}

	IAnimationDataController& Controller = AnimSequence->GetController();
	Controller.OpenBracket(NSLOCTEXT("AI4AnimationNNEEditor", "ImportClip", "Import AI4Animation clip"), false);
	Controller.InitializeModel();
	AnimSequence->ResetAnimation();
	AnimSequence->SetSkeleton(Skeleton);
	AnimSequence->SetPreviewMesh(PreviewMesh);
	Controller.SetFrameRate(FFrameRate(FMath::RoundToInt(Payload.FrameRate), 1));
	Controller.SetNumberOfFrames(FMath::Max(1, NumKeys) - 1);

	for (const TPair<FName, TArray<FVector3f>>& Pair : PositionKeys)
	{
		Controller.AddBoneCurve(Pair.Key);
		Controller.SetBoneTrackKeys(Pair.Key, Pair.Value, RotationKeys[Pair.Key], ScaleKeys[Pair.Key]);
	}

	Controller.NotifyPopulated();
	Controller.CloseBracket(false);

	AnimSequence->MarkPackageDirty();
	OutAssetPath = FString::Printf(TEXT("%s/%s"), *PackagePath, *AssetName);
	return true;
}

bool UAI4AnimationNNEEditorLibrary::ImportMannyClipFromJson(
	const FString& JsonPath,
	const FString& DestinationPackagePath,
	const FString& AssetName,
	const FString& SkeletonAssetPath,
	const FString& PreviewMeshAssetPath,
	FString& OutAssetPath,
	FString& OutErrorMessage)
{
	return ImportClipFromJson(
		JsonPath,
		DestinationPackagePath,
		AssetName,
		SkeletonAssetPath,
		PreviewMeshAssetPath,
		OutAssetPath,
		OutErrorMessage);
}
