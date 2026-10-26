package com.lifecircle.service;

import com.lifecircle.domain.*;
import com.lifecircle.repository.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.CommandLineRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.time.Instant;
import java.time.LocalDate;

/**
 * 持久化演示：向物理数据库中写入一行数据，并输出各表行数。
 * 第二次启动时数据仍然存在，用于验证文件数据库的真实持久化。
 */
@Component
@Profile("demo")
@Order(10)
public class PersistenceDemoRunner implements CommandLineRunner {
    private final String suffix = String.valueOf(System.currentTimeMillis() % 100000L);

    @Value("${persistence.exit-after-demo:false}")
    private boolean exitAfterDemo;

    private final AppUserRepository appUserRepository;
    private final UserProfileRepository userProfileRepository;
    private final ProfileTagRepository profileTagRepository;
    private final UserProfileTagRepository userProfileTagRepository;
    private final ProfileDimensionWeightRepository profileDimensionWeightRepository;
    private final DistrictRepository districtRepository;
    private final PopulationGridRepository populationGridRepository;
    private final RoadNodeRepository roadNodeRepository;
    private final RoadSegmentRepository roadSegmentRepository;
    private final FacilityCategoryRepository facilityCategoryRepository;
    private final PoiFacilityRepository poiFacilityRepository;
    private final PoiChangeLogRepository poiChangeLogRepository;
    private final ResidentAssessmentRepository residentAssessmentRepository;
    private final AssessmentDimensionRepository assessmentDimensionRepository;
    private final AssessmentFacilityStatRepository assessmentFacilityStatRepository;
    private final DistrictScoreSnapshotRepository districtScoreSnapshotRepository;
    private final SiteCandidateRepository siteCandidateRepository;
    private final SiteScoreItemRepository siteScoreItemRepository;
    private final MerchantIntentRepository merchantIntentRepository;
    private final MerchantMatchRepository merchantMatchRepository;
    private final CommunityGapRepository communityGapRepository;
    private final SimulationRecordRepository simulationRecordRepository;
    private final SyncBatchRepository syncBatchRepository;
    private final DataQualityIssueRepository dataQualityIssueRepository;
    private final OdsPoiRawRepository odsPoiRawRepository;
    private final OdsPopulationRawRepository odsPopulationRawRepository;
    private final OdsRoadRawRepository odsRoadRawRepository;

    public PersistenceDemoRunner(
            AppUserRepository appUserRepository,
            UserProfileRepository userProfileRepository,
            ProfileTagRepository profileTagRepository,
            UserProfileTagRepository userProfileTagRepository,
            ProfileDimensionWeightRepository profileDimensionWeightRepository,
            DistrictRepository districtRepository,
            PopulationGridRepository populationGridRepository,
            RoadNodeRepository roadNodeRepository,
            RoadSegmentRepository roadSegmentRepository,
            FacilityCategoryRepository facilityCategoryRepository,
            PoiFacilityRepository poiFacilityRepository,
            PoiChangeLogRepository poiChangeLogRepository,
            ResidentAssessmentRepository residentAssessmentRepository,
            AssessmentDimensionRepository assessmentDimensionRepository,
            AssessmentFacilityStatRepository assessmentFacilityStatRepository,
            DistrictScoreSnapshotRepository districtScoreSnapshotRepository,
            SiteCandidateRepository siteCandidateRepository,
            SiteScoreItemRepository siteScoreItemRepository,
            MerchantIntentRepository merchantIntentRepository,
            MerchantMatchRepository merchantMatchRepository,
            CommunityGapRepository communityGapRepository,
            SimulationRecordRepository simulationRecordRepository,
            SyncBatchRepository syncBatchRepository,
            DataQualityIssueRepository dataQualityIssueRepository,
            OdsPoiRawRepository odsPoiRawRepository,
            OdsPopulationRawRepository odsPopulationRawRepository,
            OdsRoadRawRepository odsRoadRawRepository) {
        this.appUserRepository = appUserRepository;
        this.userProfileRepository = userProfileRepository;
        this.profileTagRepository = profileTagRepository;
        this.userProfileTagRepository = userProfileTagRepository;
        this.profileDimensionWeightRepository = profileDimensionWeightRepository;
        this.districtRepository = districtRepository;
        this.populationGridRepository = populationGridRepository;
        this.roadNodeRepository = roadNodeRepository;
        this.roadSegmentRepository = roadSegmentRepository;
        this.facilityCategoryRepository = facilityCategoryRepository;
        this.poiFacilityRepository = poiFacilityRepository;
        this.poiChangeLogRepository = poiChangeLogRepository;
        this.residentAssessmentRepository = residentAssessmentRepository;
        this.assessmentDimensionRepository = assessmentDimensionRepository;
        this.assessmentFacilityStatRepository = assessmentFacilityStatRepository;
        this.districtScoreSnapshotRepository = districtScoreSnapshotRepository;
        this.siteCandidateRepository = siteCandidateRepository;
        this.siteScoreItemRepository = siteScoreItemRepository;
        this.merchantIntentRepository = merchantIntentRepository;
        this.merchantMatchRepository = merchantMatchRepository;
        this.communityGapRepository = communityGapRepository;
        this.simulationRecordRepository = simulationRecordRepository;
        this.syncBatchRepository = syncBatchRepository;
        this.dataQualityIssueRepository = dataQualityIssueRepository;
        this.odsPoiRawRepository = odsPoiRawRepository;
        this.odsPopulationRawRepository = odsPopulationRawRepository;
        this.odsRoadRawRepository = odsRoadRawRepository;
    }

    @Override
    public void run(String... args) {
        boolean empty = districtRepository.count() == 0;
        if (empty) {
            seed();
            System.out.println("[demo] 首次启动：已向物理数据库写入演示数据");
        } else {
            System.out.println("[demo] 再次启动：数据库中已有数据，跳过写入");
        }
        summary();
        if (exitAfterDemo) {
            System.exit(0);
        }
    }

    private static String unique(String prefix) {
        return prefix + System.currentTimeMillis() % 1000000L;
    }

    private void seed() {
        AppUser appUser = new AppUser();
        appUser.setUserCode(unique("USER"));
        appUser.setCreatedAt(Instant.now());
        appUser.setUpdatedAt(Instant.now());
        appUser.setPhoneHash(unique("PHON"));
        appUser = appUserRepository.save(appUser);
        Long appUserId = appUser.getId();

        UserProfile userProfile = new UserProfile();
        userProfile.setUserId(appUserId);
        userProfile.setProfileType("RESIDENT");
        userProfile.setProfileLabel("青年通勤型");
        userProfile.setCreatedAt(Instant.now());
        userProfile = userProfileRepository.save(userProfile);
        Long userProfileId = userProfile.getId();

        ProfileTag profileTag = new ProfileTag();
        profileTag.setTagCode(unique("TAG"));
        profileTag.setTagName("生鲜买菜");
        profileTag.setDimensionCode("FRESH");
        profileTag.setCreatedAt(Instant.now());
        profileTag = profileTagRepository.save(profileTag);
        Long profileTagId = profileTag.getId();

        UserProfileTag userProfileTag = new UserProfileTag();
        userProfileTag.setProfileId(userProfileId);
        userProfileTag.setTagId(profileTagId);
        userProfileTag.setSelectedAt(Instant.now());
        userProfileTag = userProfileTagRepository.save(userProfileTag);
        Long userProfileTagId = userProfileTag.getId();

        ProfileDimensionWeight profileDimensionWeight = new ProfileDimensionWeight();
        profileDimensionWeight.setProfileId(userProfileId);
        profileDimensionWeight.setDimensionCode("FRESH");
        profileDimensionWeight.setDimensionName("生鲜购物");
        profileDimensionWeight.setWeight(new BigDecimal("80"));
        profileDimensionWeight.setUpdatedAt(Instant.now());
        profileDimensionWeight = profileDimensionWeightRepository.save(profileDimensionWeight);
        Long profileDimensionWeightId = profileDimensionWeight.getId();

        District district = new District();
        district.setDistrictCode(unique("DIST"));
        district.setDistrictName("V" + suffix);
        district.setDistrictLevel("V" + suffix);
        district.setCityCode("V" + suffix);
        district.setCreatedAt(Instant.now());
        district.setUpdatedAt(Instant.now());
        district = districtRepository.save(district);
        Long districtId = district.getId();

        PopulationGrid populationGrid = new PopulationGrid();
        populationGrid.setDistrictId(districtId);
        populationGrid.setGridCode(unique("GRID"));
        populationGrid.setCenterLng(new BigDecimal("104.043100"));
        populationGrid.setCenterLat(new BigDecimal("30.642100"));
        populationGrid.setPopulation(1);
        populationGrid.setDataDate(LocalDate.now());
        populationGrid.setCreatedAt(Instant.now());
        populationGrid = populationGridRepository.save(populationGrid);
        Long populationGridId = populationGrid.getId();

        RoadNode roadNode = new RoadNode();
        roadNode.setNodeCode(unique("NODE"));
        roadNode.setLng(new BigDecimal("104.043100"));
        roadNode.setLat(new BigDecimal("30.642100"));
        roadNode.setUpdatedAt(Instant.now());
        roadNode = roadNodeRepository.save(roadNode);
        Long roadNodeId = roadNode.getId();

        RoadSegment roadSegment = new RoadSegment();
        roadSegment.setSegmentCode(unique("SEG"));
        roadSegment.setFromNodeId(roadNodeId);
        roadSegment.setToNodeId(roadNodeId);
        roadSegment.setLengthM(new BigDecimal("1"));
        roadSegment.setWalkTimeS(1);
        roadSegment.setUpdatedAt(Instant.now());
        roadSegment = roadSegmentRepository.save(roadSegment);
        Long roadSegmentId = roadSegment.getId();

        FacilityCategory facilityCategory = new FacilityCategory();
        facilityCategory.setCategoryCode(unique("CAT"));
        facilityCategory.setCategoryName("菜市场");
        facilityCategory.setDimensionCode("FRESH");
        facilityCategory.setDimensionName("生鲜购物");
        facilityCategory.setCreatedAt(Instant.now());
        facilityCategory = facilityCategoryRepository.save(facilityCategory);
        Long facilityCategoryId = facilityCategory.getId();

        PoiFacility poiFacility = new PoiFacility();
        poiFacility.setDistrictId(districtId);
        poiFacility.setCategoryId(facilityCategoryId);
        poiFacility.setPoiName(unique("POI"));
        poiFacility.setLng(new BigDecimal("104.043100"));
        poiFacility.setLat(new BigDecimal("30.642100"));
        poiFacility.setSource("MANUAL");
        poiFacility.setSourcePoiId(unique("SRC"));
        poiFacility.setFirstSeenAt(Instant.now());
        poiFacility.setLastSeenAt(Instant.now());
        poiFacility.setUpdatedAt(Instant.now());
        poiFacility = poiFacilityRepository.save(poiFacility);
        Long poiFacilityId = poiFacility.getId();

        SyncBatch syncBatch = new SyncBatch();
        syncBatch.setBatchNo(unique("BATCH"));
        syncBatch.setDataSource("AMAP");
        syncBatch.setSyncType("INCREMENT");
        syncBatch.setStartedAt(Instant.now());
        syncBatch.setCreatedAt(Instant.now());
        syncBatch = syncBatchRepository.save(syncBatch);
        Long syncBatchId = syncBatch.getId();

        PoiChangeLog poiChangeLog = new PoiChangeLog();
        poiChangeLog.setBatchId(syncBatchId);
        poiChangeLog.setChangeType("INSERT");
        poiChangeLog.setChangedAt(Instant.now());
        poiChangeLog = poiChangeLogRepository.save(poiChangeLog);
        Long poiChangeLogId = poiChangeLog.getId();

        ResidentAssessment residentAssessment = new ResidentAssessment();
        residentAssessment.setResidentCode(unique("RES"));
        residentAssessment.setDistrictId(districtId);
        residentAssessment.setTotalScore(80);
        residentAssessment.setAssessedAt(Instant.now());
        residentAssessment = residentAssessmentRepository.save(residentAssessment);
        Long residentAssessmentId = residentAssessment.getId();

        AssessmentDimension assessmentDimension = new AssessmentDimension();
        assessmentDimension.setAssessmentId(residentAssessmentId);
        assessmentDimension.setDimensionCode("FRESH");
        assessmentDimension.setDimensionName("生鲜购物");
        assessmentDimension.setDimensionScore(80);
        assessmentDimension.setWeight(new BigDecimal("80"));
        assessmentDimension = assessmentDimensionRepository.save(assessmentDimension);
        Long assessmentDimensionId = assessmentDimension.getId();

        AssessmentFacilityStat assessmentFacilityStat = new AssessmentFacilityStat();
        assessmentFacilityStat.setAssessmentId(residentAssessmentId);
        assessmentFacilityStat.setCategoryId(facilityCategoryId);
        assessmentFacilityStat = assessmentFacilityStatRepository.save(assessmentFacilityStat);
        Long assessmentFacilityStatId = assessmentFacilityStat.getId();

        DistrictScoreSnapshot districtScoreSnapshot = new DistrictScoreSnapshot();
        districtScoreSnapshot.setDistrictId(districtId);
        districtScoreSnapshot.setCoveragePct(80);
        districtScoreSnapshot.setAvgScore(new BigDecimal("80"));
        districtScoreSnapshot.setScoredAt(Instant.now());
        districtScoreSnapshot = districtScoreSnapshotRepository.save(districtScoreSnapshot);
        Long districtScoreSnapshotId = districtScoreSnapshot.getId();

        SiteCandidate siteCandidate = new SiteCandidate();
        siteCandidate.setDistrictId(districtId);
        siteCandidate.setCandidateName("东园路口");
        siteCandidate.setCreatedAt(Instant.now());
        siteCandidate = siteCandidateRepository.save(siteCandidate);
        Long siteCandidateId = siteCandidate.getId();

        SiteScoreItem siteScoreItem = new SiteScoreItem();
        siteScoreItem.setCandidateId(siteCandidateId);
        siteScoreItem.setScoreItem("V" + suffix);
        siteScoreItem.setItemScore(new BigDecimal("80"));
        siteScoreItem.setWeight(new BigDecimal("80"));
        siteScoreItem = siteScoreItemRepository.save(siteScoreItem);
        Long siteScoreItemId = siteScoreItem.getId();

        MerchantIntent merchantIntent = new MerchantIntent();
        merchantIntent.setMerchantName(unique("商户"));
        merchantIntent.setBusinessType("便利店");
        merchantIntent.setContact("13800138000");
        merchantIntent.setCreatedAt(Instant.now());
        merchantIntent.setUpdatedAt(Instant.now());
        merchantIntent = merchantIntentRepository.save(merchantIntent);
        Long merchantIntentId = merchantIntent.getId();

        CommunityGap communityGap = new CommunityGap();
        communityGap.setDistrictId(districtId);
        communityGap.setCategoryId(facilityCategoryId);
        communityGap.setAreaName("东南片区");
        communityGap.setIssue("夜间就医距离较远");
        communityGap.setGapLevel("高");
        communityGap.setCreatedAt(Instant.now());
        communityGap = communityGapRepository.save(communityGap);
        Long communityGapId = communityGap.getId();

        MerchantMatch merchantMatch = new MerchantMatch();
        merchantMatch.setIntentId(merchantIntentId);
        merchantMatch.setDistrictId(districtId);
        merchantMatch.setFitScore(80);
        merchantMatch.setMatchedAt(Instant.now());
        merchantMatch = merchantMatchRepository.save(merchantMatch);
        Long merchantMatchId = merchantMatch.getId();

        SimulationRecord simulationRecord = new SimulationRecord();
        simulationRecord.setDistrictId(districtId);
        simulationRecord.setCategoryId(facilityCategoryId);
        simulationRecord.setBeforeCoverage(80);
        simulationRecord.setAfterCoverage(80);
        simulationRecord.setBenefitedResidents(1);
        simulationRecord.setSimulatedAt(Instant.now());
        simulationRecord = simulationRecordRepository.save(simulationRecord);
        Long simulationRecordId = simulationRecord.getId();

        DataQualityIssue dataQualityIssue = new DataQualityIssue();
        dataQualityIssue.setBatchId(syncBatchId);
        dataQualityIssue.setRuleCode("DUP_POI");
        dataQualityIssue.setIssueDesc("坐标越界");
        dataQualityIssue.setSeverity("LOW");
        dataQualityIssue.setCreatedAt(Instant.now());
        dataQualityIssue = dataQualityIssueRepository.save(dataQualityIssue);
        Long dataQualityIssueId = dataQualityIssue.getId();

        OdsPoiRaw odsPoiRaw = new OdsPoiRaw();
        odsPoiRaw.setBatchId(syncBatchId);
        odsPoiRaw.setSource("MANUAL");
        odsPoiRaw.setSourcePoiId(unique("SRC"));
        odsPoiRaw.setRawJson("V" + suffix);
        odsPoiRaw.setLoadAt(Instant.now());
        odsPoiRaw = odsPoiRawRepository.save(odsPoiRaw);
        Long odsPoiRawId = odsPoiRaw.getId();

        OdsPopulationRaw odsPopulationRaw = new OdsPopulationRaw();
        odsPopulationRaw.setBatchId(syncBatchId);
        odsPopulationRaw.setGridCode(unique("GRID"));
        odsPopulationRaw.setRawJson("V" + suffix);
        odsPopulationRaw.setLoadAt(Instant.now());
        odsPopulationRaw = odsPopulationRawRepository.save(odsPopulationRaw);
        Long odsPopulationRawId = odsPopulationRaw.getId();

        OdsRoadRaw odsRoadRaw = new OdsRoadRaw();
        odsRoadRaw.setBatchId(syncBatchId);
        odsRoadRaw.setRawJson("V" + suffix);
        odsRoadRaw.setLoadAt(Instant.now());
        odsRoadRaw = odsRoadRawRepository.save(odsRoadRaw);
        Long odsRoadRawId = odsRoadRaw.getId();

    }

    private void summary() {
        System.out.println("[demo] 物理数据库各表行数：");
        System.out.println("  app_user = " + appUserRepository.count());
        System.out.println("  user_profile = " + userProfileRepository.count());
        System.out.println("  profile_tag = " + profileTagRepository.count());
        System.out.println("  user_profile_tag = " + userProfileTagRepository.count());
        System.out.println("  profile_dimension_weight = " + profileDimensionWeightRepository.count());
        System.out.println("  district = " + districtRepository.count());
        System.out.println("  population_grid = " + populationGridRepository.count());
        System.out.println("  road_node = " + roadNodeRepository.count());
        System.out.println("  road_segment = " + roadSegmentRepository.count());
        System.out.println("  facility_category = " + facilityCategoryRepository.count());
        System.out.println("  poi_facility = " + poiFacilityRepository.count());
        System.out.println("  poi_change_log = " + poiChangeLogRepository.count());
        System.out.println("  resident_assessment = " + residentAssessmentRepository.count());
        System.out.println("  assessment_dimension = " + assessmentDimensionRepository.count());
        System.out.println("  assessment_facility_stat = " + assessmentFacilityStatRepository.count());
        System.out.println("  district_score_snapshot = " + districtScoreSnapshotRepository.count());
        System.out.println("  site_candidate = " + siteCandidateRepository.count());
        System.out.println("  site_score_item = " + siteScoreItemRepository.count());
        System.out.println("  merchant_intent = " + merchantIntentRepository.count());
        System.out.println("  merchant_match = " + merchantMatchRepository.count());
        System.out.println("  community_gap = " + communityGapRepository.count());
        System.out.println("  simulation_record = " + simulationRecordRepository.count());
        System.out.println("  sync_batch = " + syncBatchRepository.count());
        System.out.println("  data_quality_issue = " + dataQualityIssueRepository.count());
        System.out.println("  ods_poi_raw = " + odsPoiRawRepository.count());
        System.out.println("  ods_population_raw = " + odsPopulationRawRepository.count());
        System.out.println("  ods_road_raw = " + odsRoadRawRepository.count());
    }
}
