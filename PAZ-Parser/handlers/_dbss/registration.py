from __future__ import annotations

from bdo_preview import register_handler

from .title.handler import TitleDbssHandler
from .titlebuff.handler import TitleBuffListHandler, TitleBuffListOffsetHandler
from .titleoffset.handler import TitleOffsetHandler
from .mentalcard.handler import MentalCardHandler, MentalCardOffsetHandler
from .detail_dialog.handler import DetailDialogHandler, DetailDialogOffsetHandler
from .base_dialog.handler import BaseDialogHandler
from .dialogtext.handler import DialogTextHandler, DialogTextOffsetHandler
from .mentaltheme.handler import MentalThemeHandler, MentalThemeOffsetHandler
from .knowledgelearning.handler import (
    KnowledgeLearningHandler,
    KnowledgeLearningOffsetHandler,
)
from .npcpersonality.handler import NpcPersonalityHandler, NpcPersonalityOffsetHandler
from .quest.handler import QuestDbssHandler
from .questgroup.handler import QuestGroupDbssHandler
from .worldquest.handler import WorldQuestDbssHandler
from .worldmapmonster.handler import WorldMapMonsterHandler, WorldMapMonsterOffsetHandler
from .cashproduct.handler import (
    CashProductHandler,
    CashProductOffsetHandler,
)
from .itemenchant.handler import (
    ItemEnchantHandler,
    ItemEnchantOffsetHandler,
)
from .journalquest.handler import JournalQuestDbssHandler, JournalQuestOffsetHandler
from .npcgift.handler import (
    NpcGiftOffsetHandler,
    NpcGiftHandler,
    NpcGiftDataOffsetHandler,
    NpcGiftDataHandler,
)
from .zodiacsign.handler import (
    ZodiacSignHandler,
    ZodiacSignOffsetHandler,
    ZodiacSignOrderHandler,
    ZodiacSignOrderOffsetHandler,
)
from .plantzone.handler import PlantZoneOffsetHandler, PlantZoneHandler
from .itemsubgroup.handler import ItemSubgroupHandler, ItemSubgroupOffsetHandler
from .characterspawntype.handler import (
    CharacterSpawnTypeOffsetHandler,
    CharacterSpawnTypeHandler,
)
from .characterobject.handler import (
    CharacterObjectOffsetHandler,
    CharacterObjectHandler,
)
from .characterstatic.handler import (
    CharacterStaticOffsetHandler,
    CharacterStaticHandler,
)
from .pet.handler import (
    PetDbssHandler,
    PetGradeHandler,
    PetGradeOffsetHandler,
    PetOffsetHandler,
)
from .petaction.handler import PetActionHandler, PetActionOffsetHandler
from .petexp.handler import PetExpHandler, PetExpOffsetHandler
from .petskill.handler import PetSkillHandler, PetSkillOffsetHandler
from .petequipskillaquire.handler import (
    PetEquipSkillAcquireHandler,
    PetEquipSkillAcquireOffsetHandler,
)
from .fairyequipskillaquire.handler import (
    FairyEquipSkillAcquireHandler,
    FairyEquipSkillAcquireOffsetHandler,
)
from .fairyskillchange.handler import (
    FairySkillChangeHandler,
    FairySkillChangeOffsetHandler,
)
from .employeename.handler import EmployeeNameHandler, EmployeeNameOffsetHandler
from .buff.handler import BuffHandler, BuffOffsetHandler
from .skill.handler import SkillHandler, SkillOffsetHandler
from .skilltype.handler import SkillTypeHandler
from .skillsimply.handler import SkillSimplyHandler
from .skillsimply.parser import parse_skillsimply_offset_rows


def register_dbss_handlers() -> None:
    register_handler("titleoffset.dbss", TitleOffsetHandler())
    register_handler("title.dbss", TitleDbssHandler())
    register_handler("titlebufflistoffset.dbss", TitleBuffListOffsetHandler())
    register_handler("titlebufflist.dbss", TitleBuffListHandler())
    register_handler("mentalcardoffset.dbss", MentalCardOffsetHandler())
    register_handler("mentalcard.dbss", MentalCardHandler())
    register_handler("detail_dialogoffset.dbss", DetailDialogOffsetHandler())
    register_handler("detail_dialog.dbss", DetailDialogHandler())
    # base_dialogoffset.dbss has the layout and keys of detail_dialogoffset.dbss.
    register_handler("base_dialogoffset.dbss", DetailDialogOffsetHandler())
    register_handler("base_dialog.dbss", BaseDialogHandler())
    register_handler("skilloffset.dbss", SkillOffsetHandler())
    register_handler("skill.dbss", SkillHandler())
    # skilltypeoffset.dbss has the layout and keys of skilloffset.dbss.
    register_handler("skilltypeoffset.dbss", SkillOffsetHandler())
    register_handler("skilltype.dbss", SkillTypeHandler())
    register_handler("skillsimplyoffset.dbss", SkillOffsetHandler(parse_skillsimply_offset_rows))
    register_handler("skillsimply.dbss", SkillSimplyHandler())
    register_handler("dialogtextoffset.dbss", DialogTextOffsetHandler())
    register_handler("dialogtext.dbss", DialogTextHandler())
    register_handler("mentalthemeoffset.dbss", MentalThemeOffsetHandler())
    register_handler("mentaltheme.dbss", MentalThemeHandler())
    register_handler("knowledgelearningoffset.dbss", KnowledgeLearningOffsetHandler())
    register_handler("knowledgelearning.dbss", KnowledgeLearningHandler())
    register_handler("npcpersonalityoffset.dbss", NpcPersonalityOffsetHandler())
    register_handler("npcpersonality.dbss", NpcPersonalityHandler())
    register_handler("quest.dbss", QuestDbssHandler())
    register_handler("questgroup.dbss", QuestGroupDbssHandler())
    register_handler("worldquest.dbss", WorldQuestDbssHandler())
    register_handler("cashproduct.dbss", CashProductHandler())
    register_handler("cashproductoffset.dbss", CashProductOffsetHandler())
    register_handler("itemenchant.dbss", ItemEnchantHandler())
    register_handler("itemenchantoffset.dbss", ItemEnchantOffsetHandler())
    register_handler("itemsubgroupoffset.dbss", ItemSubgroupOffsetHandler())
    register_handler("itemsubgroup.dbss", ItemSubgroupHandler())
    register_handler("journalquestoffset.dbss", JournalQuestOffsetHandler())
    register_handler("journalquest.dbss", JournalQuestDbssHandler())
    register_handler("npcgiftoffset.dbss", NpcGiftOffsetHandler())
    register_handler("npcgift.dbss", NpcGiftHandler())
    register_handler("npcgiftdataoffset.dbss", NpcGiftDataOffsetHandler())
    register_handler("npcgiftdata.dbss", NpcGiftDataHandler())
    register_handler("zodiacsignoffset.dbss", ZodiacSignOffsetHandler())
    register_handler("zodiacsign.dbss", ZodiacSignHandler())
    register_handler("zodiacsignorderoffset.dbss", ZodiacSignOrderOffsetHandler())
    register_handler("zodiacsignorder.dbss", ZodiacSignOrderHandler())
    register_handler("plantzoneoffset.dbss", PlantZoneOffsetHandler())
    register_handler("plantzone.dbss", PlantZoneHandler())
    register_handler("characterspawntypeoffset.dbss", CharacterSpawnTypeOffsetHandler())
    register_handler("characterspawntype.dbss", CharacterSpawnTypeHandler())
    register_handler("characterobjectoffset.dbss", CharacterObjectOffsetHandler())
    register_handler("characterobject.dbss", CharacterObjectHandler())
    register_handler("characterstaticoffset.dbss", CharacterStaticOffsetHandler())
    register_handler("characterstatic.dbss", CharacterStaticHandler())
    register_handler("petoffset.dbss", PetOffsetHandler())
    register_handler("petgradeoffset.dbss", PetGradeOffsetHandler())
    register_handler("petgrade.dbss", PetGradeHandler())
    register_handler("pet.dbss", PetDbssHandler())
    register_handler("petactionoffset.dbss", PetActionOffsetHandler())
    register_handler("petaction.dbss", PetActionHandler())
    register_handler("petexpoffset.dbss", PetExpOffsetHandler())
    register_handler("petexp.dbss", PetExpHandler())
    register_handler("petskilloffset.dbss", PetSkillOffsetHandler())
    register_handler("petskill.dbss", PetSkillHandler())
    register_handler(
        "petequipskillaquireoffset.dbss",
        PetEquipSkillAcquireOffsetHandler(),
    )
    register_handler("petequipskillaquire.dbss", PetEquipSkillAcquireHandler())
    register_handler(
        "fairyequipskillaquireoffset.dbss",
        FairyEquipSkillAcquireOffsetHandler(),
    )
    register_handler("fairyequipskillaquire.dbss", FairyEquipSkillAcquireHandler())
    register_handler(
        "fairyskillchangeoffset.dbss",
        FairySkillChangeOffsetHandler(),
    )
    register_handler("fairyskillchange.dbss", FairySkillChangeHandler())
    register_handler("employeenameoffset.dbss", EmployeeNameOffsetHandler())
    register_handler("employeename.dbss", EmployeeNameHandler())
    register_handler("buffoffset.dbss", BuffOffsetHandler())
    register_handler("buff.dbss", BuffHandler())
    register_handler("worldmapmonsteroffset.dbss", WorldMapMonsterOffsetHandler())
    register_handler("worldmapmonster.dbss", WorldMapMonsterHandler())
