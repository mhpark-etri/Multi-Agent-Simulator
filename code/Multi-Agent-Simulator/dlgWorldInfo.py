# -*- coding: utf-8 -*-
"""World 정보 팝업 — 선택한 월드의 설명 / 출처 / 라이선스를 보여준다.

World 패널에서 고른 월드가 실제로 어느 파일을 쓰고, 어디서 왔으며, 어떤
라이선스인지 확인하기 위한 창이다.

표시 원칙 두 가지.

1. 라이선스는 추측해서 채우지 않는다. 근거를 함께 밝힌다.
     로컬 확인   — 이 저장소나 이미지 안의 LICENSE / copyright 파일을 읽어 확인
     업스트림 표기 — 배포처 문서 기준. 직접 읽어 확인하지는 못함
     확인 필요   — 확인하지 못함 (빈칸으로 두지 말고 그대로 표시)

2. '파일이 지금 있는가'(설치 상태)와 '누가 그 파일을 주는가'(제공 방식)는
   다른 질문이므로 따로 표시한다. 예를 들어 cafe.world 는 이 저장소가 배포하지
   않지만 apt 패키지 gazebo11-common 이 깔아주므로 사용자가 할 일은 없다.

모든 문구는 (한글, 영문) 짝으로 두고 창을 열 때 언어에 맞춰 고른다.
"""

import os
from PySide6 import QtWidgets, QtCore


# ── 제공 방식 ──────────────────────────────────────────────────────────────
PROV_BUNDLED = ('이 저장소에 동봉 — 별도 작업 불필요',
                'Bundled in this repository — nothing for you to do')
PROV_APT = ('ROS/Gazebo apt 패키지(gazebo11-common)가 설치 — 별도 작업 불필요',
            'Installed by the ROS/Gazebo apt package (gazebo11-common) — nothing for you to do')
PROV_USER = ('사용자가 직접 내려받아 worlds/ 에 넣어야 함',
             'You must download it yourself and place it in worlds/')

# ── 라이선스 확인 근거 ──────────────────────────────────────────────────────
EV_LOCAL = ('로컬 확인 — 저장소나 이미지 안의 라이선스 파일을 직접 읽음',
            'Verified locally — read the license file in the repository or image')
EV_UPSTREAM_FILE = ('업스트림 확인 — 배포처 저장소의 LICENSE 원문을 직접 읽음',
                    "Verified upstream — read the LICENSE file in the distributor's own repository")
EV_UPSTREAM = ('업스트림 표기 — 배포처 문서 기준, 직접 확인하지 못함',
               'As documented upstream — not verified from a local file')
EV_UNKNOWN = ('확인 필요 — 확인하지 못함',
              'Not determined')

_UNKNOWN_TXT = ('확인 필요', 'Not determined')

_STOCK_DIR = '/usr/share/gazebo-11/worlds'
_PROJ_DIR = '/root/tesla/ros/navi/worlds'


# ── 출처/라이선스 표 ────────────────────────────────────────────────────────
# key   = World 패널 서브카테고리 이름
# 값은 모두 (한글, 영문) 짝. path 만 문자열.
_GAZEBO_CLASSIC = dict(
    desc=('Gazebo Classic 이 기본 제공하는 월드입니다.',
          'A world shipped with Gazebo Classic.'),
    source=('https://github.com/gazebosim/gazebo-classic',
            'https://github.com/gazebosim/gazebo-classic'),
    license=('Apache License 2.0', 'Apache License 2.0'),
    evidence=EV_LOCAL,
    provision=PROV_APT,
    note=('ROS Noetic 을 설치할 때 apt 패키지 gazebo11-common 으로 함께 깔립니다. '
          '이 저장소가 배포하는 파일은 아니지만 사용자가 따로 받을 필요도 없습니다.\n'
          '라이선스 근거는 이미지 안의 /usr/share/doc/gazebo11-common/copyright 입니다.\n'
          '월드가 부르는 3D 모델은 별도로 models.gazebosim.org 에서 내려받으며 '
          'CC BY 3.0 입니다.',
          'It arrives with the apt package gazebo11-common when ROS Noetic is installed. '
          'This repository does not distribute it, but you do not need to fetch it either.\n'
          'License evidence: /usr/share/doc/gazebo11-common/copyright inside the image.\n'
          'The 3D models it references are downloaded separately from models.gazebosim.org '
          'and are CC BY 3.0.'),
)

# ── 공개 수집처(leonhartyao) 를 거쳐 오는 월드들 ────────────────────────────
# 중요 — 수집 저장소의 루트 LICENSE 를 그 안에 모인 개별 파일의 라이선스로
# 그대로 대입하면 안 된다. 이 수집처는 readme 의 'Source' 절에서 원출처 여섯 곳
# (3DGEMS / RotorS / TU Delft / ARTI-Robots / Clearpath Robotics / Fetch Robotics)
# 을 스스로 밝히고 있으며, 원저작물의 라이선스는 각 upstream 을 따른다.
# 따라서 원출처별로 나누어 표시하고, 특정하지 못한 것은 '확인 필요' 로 남긴다.
_COLLECTOR = 'https://github.com/leonhartyao/gazebo_models_worlds_collection'

_COLLECTOR_TAIL = (
    '\n이 저장소에도 이미지에도 들어 있지 않습니다. 아래 수집처에서 내려받아 '
    'worlds/ 폴더에 넣어야 실행됩니다.\n'
    f'수집처: {_COLLECTOR} (저장소 루트 LICENSE 는 GPL-3.0)\n'
    '수집처 루트가 GPL-3.0 이라는 사실과, 그 안의 개별 파일이 GPL 로 재라이선스되었다는 '
    '주장은 서로 다른 이야기입니다. 재배포하려면 위 원출처의 조건을 직접 확인하십시오.',
    '\nIncluded in neither this repository nor the image. Download it from the collection '
    'below into the worlds/ folder before use.\n'
    f'Collection: {_COLLECTOR} (its repository-root LICENSE is GPL-3.0)\n'
    'That the collection root is GPL-3.0 is a different claim from the individual files '
    'having been relicensed under GPL. Check the upstream terms above before redistributing.')


def _collected(desc_ko, desc_en, origin, lic_ko, lic_en, evidence, note_ko='', note_en=''):
    """수집처를 거쳐 오는 월드. 원출처와 수집처를 분리해 표시한다."""
    return dict(
        desc=(desc_ko, desc_en),
        source=(origin, origin),
        license=(lic_ko, lic_en),
        evidence=evidence,
        provision=PROV_USER,
        note=((note_ko or '') + _COLLECTOR_TAIL[0], (note_en or '') + _COLLECTOR_TAIL[1]),
    )


_ORIGIN_FETCH = 'https://github.com/fetchrobotics/fetch_gazebo (fetchit_challenge)'
_ORIGIN_DELFT = 'https://github.com/tudelft/gazebo_models'
_ORIGIN_CPR = 'https://github.com/clearpathrobotics/cpr_gazebo (cpr_office_gazebo)'
_ORIGIN_ROTORS = 'https://github.com/ethz-asl/rotors_simulator (rotors_gazebo)'
_ORIGIN_3DGEMS = 'http://data.nvision2.eecs.yorku.ca/3DGEMS/'

_MLHERD = dict(
    desc=('공개 월드 수집처에서 가져오는 사무실 월드입니다.',
          'An office world taken from a public world collection.'),
    source=('https://github.com/mlherd/Dataset-of-Gazebo-Worlds-Models-and-Maps',
            'https://github.com/mlherd/Dataset-of-Gazebo-Worlds-Models-and-Maps'),
    license=('확인 필요 — 업스트림이 라이선스를 선언하지 않음',
             'Not determined — the upstream repository declares no license'),
    evidence=EV_UNKNOWN,
    provision=PROV_USER,
    note=('이 저장소에도 이미지에도 들어 있지 않습니다. 위 수집처에서 내려받아야 합니다.\n'
          '※ 출처 주의 — 위 수집처의 README 는 이 월드를 "AWS Office" 라고 부르지만, '
          'AWS 가 공개한 저장소를 확인하지 못했습니다(aws-robotics 조직 저장소 43개와 '
          'GitHub 검색 모두 0건). AWS 가 공개한 Gazebo 월드는 warehouse / hospital / '
          'small house / bookstore / racetrack 다섯 개뿐입니다.\n'
          '따라서 이 월드는 이 수집처가 유일하게 확인되는 배포처이고, 그 저장소에는 '
          '라이선스 선언도 라이선스 파일도 없습니다(압축 파일 내부까지 확인). '
          '재배포 조건을 단정할 수 없으므로 사용 전에 배포처에 확인하십시오.\n'
          '월드가 office_part1.zip / office_part2.zip 으로 나뉘어 있어 풀어서 합쳐야 합니다.',
          'Included in neither this repository nor the image; download it from the '
          'collection above.\n'
          'PROVENANCE WARNING — that collection\'s README calls this world "AWS Office", but '
          'no public AWS repository for it could be found (zero hits across the 43 '
          'aws-robotics repositories and a GitHub search). The Gazebo worlds AWS published '
          'are only warehouse, hospital, small house, bookstore and racetrack.\n'
          'So this collection is the only confirmed source, and it declares no license and '
          'ships no license file (verified inside the archives too). Redistribution terms '
          'cannot be stated — check with the upstream before use.\n'
          'The world is split across office_part1.zip / office_part2.zip and must be '
          'unpacked and combined.'),
)

_UNKNOWN = dict(
    desc=('', ''),
    source=_UNKNOWN_TXT,
    license=_UNKNOWN_TXT,
    evidence=EV_UNKNOWN,
    provision=PROV_USER,
    note=('출처를 확인하지 못했습니다. 이 저장소에도 이미지에도 들어 있지 않으므로 '
          'README 에 적힌 수집처들에서 직접 찾아 내려받아야 합니다.',
          'The origin could not be determined. It is in neither this repository nor the '
          'image, so you must locate and download it from one of the collections listed '
          'in the README.'),
)

_WORLD_INFO = {
    # ── Custom : 협업 태스크용 ──────────────────────────────────────────
    'collaboration': dict(
        desc=('AWS RoboMaker 소형 창고. 선반·팔레트·적재물이 있는 실내 물류 환경입니다.',
              'AWS RoboMaker small warehouse — an indoor logistics environment with '
              'shelves, pallets and clutter.'),
        path=os.path.join(_PROJ_DIR, 'no_roof_small_warehouse.world'),
        source=('https://github.com/aws-robotics/aws-robomaker-small-warehouse-world',
                'https://github.com/aws-robotics/aws-robomaker-small-warehouse-world'),
        license=('MIT-0 (MIT No Attribution)', 'MIT-0 (MIT No Attribution)'),
        evidence=EV_LOCAL,
        provision=PROV_BUNDLED,
        note=('원본 에셋을 수정 없이 동봉했습니다. 월드 파일은 ros/navi/worlds/ 에, '
              '모델 14개는 models/ 에 있으며 init.sh 가 ~/.gazebo/models 로 복사합니다. '
              '별도 다운로드나 패키지 빌드가 필요 없습니다.\n'
              '라이선스 전문: licenses/aws-robomaker-small-warehouse-world-MIT-0.txt\n'
              'LICENSE 본문이 SPDX 표준 MIT-0 원문과 완전히 일치함을 확인했습니다'
              '(공백 정규화, 저작권 고지줄 제외).\n'
              '참고 — 원본 LICENSE 파일은 MIT-0 이지만 원본 package.xml 은 Apache 2.0 '
              '으로 다르게 적혀 있습니다. 둘 다 허용형입니다.',
              'Vendored unmodified. The world lives in ros/navi/worlds/ and its 14 models '
              'in models/, which init.sh copies into ~/.gazebo/models — no separate '
              'download or package build is needed.\n'
              'Full text: licenses/aws-robomaker-small-warehouse-world-MIT-0.txt\n'
              'The body of the LICENSE was checked against the SPDX canonical MIT-0 text and '
              'matches exactly (whitespace-normalised, copyright notice excluded).\n'
              'Note: the upstream LICENSE file is MIT-0 while the upstream package.xml '
              'declares Apache 2.0. Both are permissive.'),
    ),
    'collaboration_empty': dict(
        desc=('외벽만 있는 빈 창고(14.3 × 21.15 m). 장애물이 없어 물리 연산이 가볍고 '
              '실시간 계수(RTF)가 높습니다. 릴레이·다목적 이동에서 고를 수 있습니다.',
              'An empty warehouse with outer walls only (14.3 × 21.15 m). No clutter, so '
              'physics is cheap and the real-time factor is high. Selectable for the '
              'Relay and Multi-Goal Move tasks.'),
        path=os.path.join(_PROJ_DIR, 'empty_warehouse_walls.world'),
        source=('이 저장소 자체 제작 (ETRI)', 'Authored in this repository (ETRI)'),
        license=('Apache License 2.0 — Copyright 2024-2026 ETRI',
                 'Apache License 2.0 — Copyright 2024-2026 ETRI'),
        evidence=EV_LOCAL,
        provision=PROV_BUNDLED,
        note=('기본 도형(box)만으로 구성되어 있고 외부 에셋을 참조하지 않습니다.',
              'Built from primitive boxes only; it references no external assets.'),
    ),
    'collaboration_bnt': dict(
        desc=('칸막이가 있는 실내 구획 환경. 충돌회피·지도제작·물건찾기 태스크가 '
              '이 월드를 사용합니다.',
              'A partitioned indoor environment. Used by the Collision Avoidance, '
              'Distributed Mapping and Find Object tasks.'),
        path=os.path.join(_PROJ_DIR, 'bnt_partition_scaled.world'),
        source=('이 저장소 자체 제작 (ETRI)', 'Authored in this repository (ETRI)'),
        license=('Apache License 2.0 — Copyright 2024-2026 ETRI',
                 'Apache License 2.0 — Copyright 2024-2026 ETRI'),
        evidence=EV_LOCAL,
        provision=PROV_BUNDLED,
        note=('물건찾기 태스크는 책상을 추가한 파생 월드 '
              'bnt_partition_scaled_aligned_desk_v3.world 를 씁니다.',
              'The Find Object task uses a derived world that adds desks: '
              'bnt_partition_scaled_aligned_desk_v3.world.'),
    ),
}

# 그룹 단위로 붙는 항목들
for _n in ('cafe', 'willowgarage', 'osrf_elevator'):
    _WORLD_INFO[_n] = dict(_GAZEBO_CLASSIC)
# Fetch Robotics 유래 — upstream package.xml 은 <license>BSD</license> 로만 선언한다.
# BSD 는 변형이 여럿이므로 임의로 BSD-3-Clause 라고 좁히지 않는다.
for _n in ('fetchit_challenge_arena_montreal2019',
           'fetchit_challenge_arena_montreal2019_highlights',
           'fetchit_challenge_arena_montreal2019_onlylights',
           'fetchit_challenge_assembly', 'fetchit_challenge_atrezzo',
           'fetchit_challenge_simple', 'fetchit_challenge_simple_highlights',
           'fetchit_challenge_tests', 'fetchit_challenge_tests_lowlights'):
    _WORLD_INFO[_n] = _collected(
        'FetchIt 챌린지 아레나 월드입니다.', 'A FetchIt challenge arena world.',
        _ORIGIN_FETCH,
        'BSD (변형 미상) — upstream package.xml 표기',
        'BSD (variant unspecified) — as declared in the upstream package.xml',
        EV_UPSTREAM_FILE)

# TU Delft 유래 — upstream 저장소 자체가 GPL-3.0 이다.
for _n in ('cyberzoo', 'cyberzoo2019_orange_poles', 'cyberzoo2019_orange_poles_panels',
           'cyberzoo2019_ralphthesis2020', 'cyberzoo_orange_poles', 'cyberzoo_panel'):
    _WORLD_INFO[_n] = _collected(
        'TU Delft CyberZoo 실험 공간 월드입니다.',
        'A world of the TU Delft CyberZoo test space.',
        _ORIGIN_DELFT, 'GPL-3.0', 'GPL-3.0', EV_UPSTREAM_FILE)

_WORLD_INFO['cyberzoo_4_panels'] = _collected(
    'TU Delft CyberZoo 실험 공간 월드입니다.',
    'A world of the TU Delft CyberZoo test space.',
    _ORIGIN_DELFT, 'GPL-3.0', 'GPL-3.0', EV_UPSTREAM_FILE,
    note_ko='※ 이 파일은 현재 upstream 사본과 내용이 일치하지 않습니다. '
            '어느 리비전에서 온 것인지는 확인하지 못했습니다.',
    note_en='NOTE: this file does not match the current upstream copy; the exact upstream '
            'revision it came from has not been determined.')

# Clearpath Robotics 유래 — upstream cpr_office_gazebo/package.xml 은 BSD 선언.
for _n in ('office_cpr', 'office_cpr_construction'):
    _WORLD_INFO[_n] = _collected(
        'Clearpath 사무실 환경 월드입니다.', 'A Clearpath office environment world.',
        _ORIGIN_CPR,
        'BSD (변형 미상) — upstream package.xml 표기',
        'BSD (variant unspecified) — as declared in the upstream package.xml',
        EV_UPSTREAM_FILE,
        note_ko='※ 원출처는 수집처의 커밋 기록("add models and worlds from cpr_gazebo")으로 '
                '확인했습니다. 다만 수집본은 원본 .world 를 그대로 복사한 것이 아니라 '
                'Gazebo 에서 내보낸 형태로 보이며, 정확한 원본 파일은 특정하지 못했습니다.',
        note_en='NOTE: the origin was established from the collection\'s commit message '
                '("add models and worlds from cpr_gazebo"). The collected copy looks like a '
                'world exported from Gazebo rather than a verbatim copy of an upstream '
                '.world, and the exact source file was not identified.')

# RotorS 유래 — upstream rotors_gazebo/package.xml 은 'ASL 2.0' 으로 표기한다.
# 통상 Apache Software License 2.0 을 뜻하지만, upstream 표기를 그대로 남긴다.
for _n in ('powerplant', 'warehouse'):
    _WORLD_INFO[_n] = _collected(
        'RotorS 시뮬레이터에서 온 월드입니다.', 'A world from the RotorS simulator.',
        _ORIGIN_ROTORS,
        'ASL 2.0 — upstream package.xml 표기 (통상 Apache-2.0 을 뜻함)',
        'ASL 2.0 — as declared in the upstream package.xml (commonly meaning Apache-2.0)',
        EV_UPSTREAM_FILE,
        note_ko='※ 수집본은 원본과 내용이 달라, 수집 과정에서 수정된 사본으로 보입니다.',
        note_en='NOTE: the collected copy differs from upstream and appears to have been '
                'modified during collection.')

# 3DGEMS 유래 — 이 월드가 부르는 모델들의 model.config 저작자가
# Amir Rasouli (York University, 3DGEMS 제작자) 로 기록돼 있다.
_WORLD_INFO['workshop_example'] = _collected(
    '작업장 예제 월드입니다.', 'A workshop example world.',
    _ORIGIN_3DGEMS,
    '확인 필요 — 아래 비고 참조', 'Not determined — see the notes below',
    EV_UNKNOWN,
    note_ko='※ 이 월드가 부르는 모델(Box_15x30, Workshop, Wire_Shelf 등)의 model.config '
            '저작자가 Amir Rasouli (York University) 로 기록돼 있어 3DGEMS 유래로 보입니다.\n'
            '다만 3DGEMS 는 스스로 "대부분의 3D 메시를 3D Warehouse 에서 수집했고 직접 '
            '설계한 것이 아니다" 라고 밝히고 있습니다. 즉 출처를 3DGEMS 로 좁혀도 개별 '
            '메시의 권리관계는 별도로 확인해야 합니다.',
    note_en='NOTE: the models it references (Box_15x30, Workshop, Wire_Shelf, ...) carry '
            'Amir Rasouli (York University) as the author in their model.config, which points '
            'to 3DGEMS.\n'
            'However 3DGEMS itself states that most of its 3D meshes were collected from '
            '3D Warehouse rather than authored by them, so narrowing the origin to 3DGEMS '
            'does not settle the rights of the individual meshes.')

# 원출처를 특정하지 못한 것 — 추정하지 않고 그대로 남긴다.
_WORLD_INFO['office_small'] = _collected(
    '소형 사무실 월드입니다.', 'A small office world.',
    _COLLECTOR,
    '확인 필요 — 원출처를 특정하지 못함', 'Not determined — the origin was not identified',
    EV_UNKNOWN,
    note_ko='※ 수집처가 밝힌 원출처 여섯 곳(3DGEMS / RotorS / TU Delft / ARTI-Robots / '
            'Clearpath / Fetch) 중 어디에서 왔는지 확인하지 못했습니다. 이 월드가 부르는 '
            '모델들은 model.config 의 저작자 필드가 비어 있습니다.',
    note_en='NOTE: it could not be determined which of the six upstream projects the '
            'collection names (3DGEMS / RotorS / TU Delft / ARTI-Robots / Clearpath / Fetch) '
            'this came from. The models it references have empty author fields in their '
            'model.config.')
for _n in ('office',):
    # office 는 mlherd README 가 'AWS Office' 라 부르지만 AWS 공개 저장소를 확인하지
    # 못했다(aws-robotics 조직 저장소 43개, GitHub 검색 모두 0건). 근거가 없으므로
    # 수집처만 적고 라이선스는 '확인 필요' 로 남긴다.
    _WORLD_INFO[_n] = dict(_MLHERD)


# ── AWS RoboMaker 원본이 확인된 월드 ────────────────────────────────────────
# mlherd 수집처도 같은 파일을 재호스팅하지만 라이선스 파일이 하나도 들어 있지
# 않다(zip 4개 1,490개 항목 확인, 0건). 원본인 AWS 저장소에는 MIT-0 LICENSE 가
# 실제로 들어 있고 직접 읽어 확인했으므로, 원본 쪽을 출처로 적는다.
def _aws_world(desc_ko, desc_en, repo, note_ko='', note_en=''):
    base_ko = ('저장소에 포함되어 있지 않습니다. 위 AWS 저장소에서 받으십시오 — '
               '파일은 `ros1` 브랜치에 있습니다(기본 브랜치는 `archive`).\n'
               '공개 수집처(mlherd/Dataset-of-Gazebo-Worlds-Models-and-Maps)가 같은 파일을 '
               '재호스팅하지만 라이선스 파일이 들어 있지 않으므로, AWS 에서 직접 받는 편이 '
               '근거가 확실합니다.\n'
               '받는 방법은 README 의 "AWS RoboMaker 월드" 절을 보십시오.')
    base_en = ('Not included in this repository — get it from the AWS repository above. '
               'The files live on the `ros1` branch (the default branch is `archive`).\n'
               'A public collection (mlherd/Dataset-of-Gazebo-Worlds-Models-and-Maps) re-hosts '
               'the same files but ships no license file, so obtaining it from AWS directly '
               'rests on firmer ground.\n'
               'See the "AWS RoboMaker worlds" section of the README for the steps.')
    return dict(
        desc=(desc_ko, desc_en),
        source=(repo, repo),
        license=('MIT-0 (MIT No Attribution)', 'MIT-0 (MIT No Attribution)'),
        # 이 월드는 여기에 동봉하지 않으므로, 확인한 LICENSE 는 이 저장소가 아니라
        # AWS 저장소의 것이다. '로컬 확인' 으로 적으면 아래 '제공 방식' 과 어긋난다.
        evidence=EV_UPSTREAM_FILE,
        provision=PROV_USER,
        note=((note_ko + '\n' if note_ko else '') + base_ko,
              (note_en + '\n' if note_en else '') + base_en),
    )


_AWS_HOSPITAL = 'https://github.com/aws-robotics/aws-robomaker-hospital-world'
_AWS_HOUSE = 'https://github.com/aws-robotics/aws-robomaker-small-house-world'

_WORLD_INFO['hospital'] = _aws_world(
    'AWS RoboMaker 병원. 병실·복도·의료 장비가 있는 실내 환경입니다.',
    'AWS RoboMaker hospital — an indoor environment with wards, corridors and medical equipment.',
    _AWS_HOSPITAL)
_WORLD_INFO['small_house'] = _aws_world(
    'AWS RoboMaker 주택. 방이 여러 개이고 가구가 배치된 실내 환경입니다.',
    'AWS RoboMaker small house — a multi-room interior furnished throughout.',
    _AWS_HOUSE)
for _n, _fl in (('hospital_2_floors', ('hospital_two_floors.world', '2층', 'two-floor')),
                ('hospital_3_floors', ('hospital_three_floors.world', '3층', 'three-floor'))):
    _WORLD_INFO[_n] = _aws_world(
        f'AWS RoboMaker 병원 {_fl[1]} 버전입니다.',
        f'The {_fl[2]} variant of the AWS RoboMaker hospital.',
        _AWS_HOSPITAL,
        note_ko=(f'※ 파일 이름을 바꿔야 합니다. AWS 는 {_fl[0]} 로 배포하는데 '
                 f'이 항목은 {_n}.world 를 찾습니다.'),
        note_en=(f'NOTE: the file must be renamed. AWS ships it as {_fl[0]} '
                 f'while this entry looks for {_n}.world.'))

_WORLD_INFO['factory'] = dict(
    desc=('공개 수집처 제작자가 직접 만든 공장 월드입니다.',
          'A factory world authored by the maintainer of a public collection.'),
    source=('https://github.com/mlherd/Dataset-of-Gazebo-Worlds-Models-and-Maps',
            'https://github.com/mlherd/Dataset-of-Gazebo-Worlds-Models-and-Maps'),
    license=('확인 필요 — 업스트림이 라이선스를 선언하지 않음',
             'Not determined — the upstream repository declares no license'),
    evidence=EV_UNKNOWN,
    provision=PROV_USER,
    note=('AWS 월드가 아닙니다. 위 저장소의 README 가 "Custom Factory" 라고 적고 있어 '
          '수집처 제작자의 자작으로 보입니다.\n'
          '저장소에 라이선스 선언이 없고 파일 안에도 라이선스가 들어 있지 않아 재배포 '
          '조건을 단정할 수 없습니다. 사용 전에 배포처에 확인하십시오.\n'
          '월드 파일 이름이 factory.model 이라 이 항목이 찾는 factory.world 와 다릅니다.',
          'This is not an AWS world. The upstream README calls it "Custom Factory", so it '
          'appears to be authored by the collection maintainer.\n'
          'The repository declares no license and the files carry none, so redistribution '
          'terms cannot be stated. Check with the upstream before use.\n'
          'The world file is named factory.model, which differs from the factory.world this '
          'entry looks for.'))


def world_info(sub_name):
    """서브카테고리 이름으로 정보 항목을 찾는다. 모르는 이름은 _UNKNOWN 으로."""
    info = dict(_WORLD_INFO.get(sub_name, _UNKNOWN))
    if not info.get('path'):
        # 스톡 규칙: launch 에 worlds/<name>.world 로 들어가 gazebo 검색경로에서 찾는다
        info['path'] = os.path.join(_STOCK_DIR, sub_name + '.world')
    return info


def _pick(pair, ko):
    """(한글, 영문) 짝에서 하나를 고른다. 짝이 아니면 그대로 돌려준다."""
    if isinstance(pair, (tuple, list)) and len(pair) == 2:
        return pair[0] if ko else pair[1]
    return pair


class DialogWorldInfo(QtWidgets.QDialog):
    """선택한 월드의 정보·출처·라이선스를 보여주는 읽기 전용 팝업."""

    def __init__(self, parent=None, main_name='', sub_name='', ko=True):
        super().__init__(parent)
        self.m_ko = ko
        info = world_info(sub_name)

        self.setWindowTitle('월드 정보 (World Info)' if ko else 'World Info')
        self.setMinimumWidth(640)

        root = QtWidgets.QVBoxLayout(self)

        title = QtWidgets.QLabel(f'{main_name} › {sub_name}' if main_name else sub_name)
        f = title.font()
        f.setPointSize(f.pointSize() + 3)
        f.setBold(True)
        title.setFont(f)
        root.addWidget(title)

        desc = _pick(info.get('desc', ('', '')), ko)
        if desc:
            lbDesc = QtWidgets.QLabel(desc)
            lbDesc.setWordWrap(True)
            lbDesc.setStyleSheet('color:#555;')
            root.addWidget(lbDesc)

        box = QtWidgets.QGroupBox()
        grid = QtWidgets.QGridLayout(box)
        grid.setColumnStretch(1, 1)
        self._row = 0

        if os.path.exists(info['path']):
            state = '이 컴퓨터에 있음' if ko else 'present on this machine'
            state_style = 'color:#2e7d32;'
        else:
            state = ('이 컴퓨터에 없음' if ko else 'not on this machine')
            state_style = 'color:#c62828;'

        self._add(grid, '월드 파일' if ko else 'World file', info['path'], mono=True)
        self._add(grid, '설치 상태' if ko else 'Status', state, style=state_style)
        self._add(grid, '제공 방식' if ko else 'Provided by',
                  _pick(info['provision'], ko))
        self._add(grid, '출처' if ko else 'Source', _pick(info['source'], ko), link=True)
        self._add(grid, '라이선스' if ko else 'License', _pick(info['license'], ko))
        self._add(grid, '확인 근거' if ko else 'Evidence', _pick(info['evidence'], ko))
        root.addWidget(box)

        note = _pick(info.get('note', ('', '')), ko)
        if note:
            lbNoteTitle = QtWidgets.QLabel('비고' if ko else 'Notes')
            lbNoteTitle.setStyleSheet('font-weight:bold;')
            root.addWidget(lbNoteTitle)
            txt = QtWidgets.QPlainTextEdit(note)
            txt.setReadOnly(True)
            txt.setMinimumHeight(110)
            root.addWidget(txt)

        foot = QtWidgets.QLabel(
            '전체 제3자 구성요소 목록은 저장소의 NOTICE 파일에 있습니다.'
            if ko else
            'The full list of third-party components is in the repository NOTICE file.')
        foot.setStyleSheet('color:#888;')
        foot.setWordWrap(True)
        root.addWidget(foot)

        btns = QtWidgets.QHBoxLayout()
        btns.addStretch(1)
        btnClose = QtWidgets.QPushButton('닫기' if ko else 'Close')
        btnClose.clicked.connect(self.accept)
        btns.addWidget(btnClose)
        root.addLayout(btns)

    def _add(self, grid, label, value, link=False, mono=False, style=''):
        lb = QtWidgets.QLabel(label)
        lb.setStyleSheet('color:#555;')
        lb.setAlignment(QtCore.Qt.AlignTop | QtCore.Qt.AlignLeft)
        if link and str(value).startswith('http'):
            val = QtWidgets.QLabel(f'<a href="{value}">{value}</a>')
            val.setOpenExternalLinks(True)
        else:
            val = QtWidgets.QLabel(str(value))
        val.setWordWrap(True)
        val.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        css = style
        if mono:
            css += 'font-family:monospace;'
        if css:
            val.setStyleSheet(css)
        grid.addWidget(lb, self._row, 0)
        grid.addWidget(val, self._row, 1)
        self._row += 1
