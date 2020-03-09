"""
The Sims 4 Community Library is licensed under the Creative Commons Attribution 4.0 International public license (CC BY 4.0).
https://creativecommons.org/licenses/by/4.0/
https://creativecommons.org/licenses/by/4.0/legalcode

Copyright (c) COLONOLNUTTY
"""
import math

import sims4.commands
from typing import Tuple, Any, Callable, Union, Iterator

from pprint import pformat

from distributor.shared_messages import IconInfoData
from protocolbuffers.Localization_pb2 import LocalizedString
from sims.sim_info import SimInfo
from sims4communitylib.dialogs.common_choice_outcome import CommonChoiceOutcome
from sims4communitylib.dialogs.common_choose_dialog import CommonChooseDialog
from sims4communitylib.dialogs.custom_dialogs.picker_dialogs.common_ui_object_category_picker import \
    CommonUiObjectCategoryPicker

from sims4communitylib.dialogs.option_dialogs.options.objects.common_dialog_option_category import \
    CommonDialogObjectOptionCategory
from sims4communitylib.dialogs.utils.common_dialog_utils import CommonDialogUtils
from sims4communitylib.enums.strings_enum import CommonStringId
from sims4communitylib.exceptions.common_exceptions_handler import CommonExceptionHandler
from sims4communitylib.mod_support.mod_identity import CommonModIdentity
from sims4communitylib.modinfo import ModInfo
from sims4communitylib.utils.common_function_utils import CommonFunctionUtils
from sims4communitylib.utils.common_icon_utils import CommonIconUtils
from sims4communitylib.utils.localization.common_localized_string_colors import CommonLocalizedStringColor
from sims4communitylib.utils.localization.common_localization_utils import CommonLocalizationUtils
from sims4communitylib.utils.sims.common_sim_utils import CommonSimUtils
from ui.ui_dialog_picker import UiObjectPicker, ObjectPickerRow


class CommonChooseObjectDialog(CommonChooseDialog):
    """CommonChooseObjectDialog(\
        title_identifier,\
        description_identifier,\
        choices,\
        title_tokens=(),\
        description_tokens=(),\
        per_page=25,\
        mod_identity=None\
    )

    Create a dialog that prompts the player to choose an object.

    .. note:: To see an example dialog, run the command :class:`s4clib_testing.show_choose_object_dialog` in the in-game console.

    .. highlight:: python
    .. code-block:: python

        def _common_testing_show_choose_object_dialog():

            def _on_chosen(choice: str, outcome: CommonChoiceOutcome):
                pass

            # LocalizedStrings within other LocalizedStrings
            title_tokens = (CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_SOME_TEXT_FOR_TESTING, text_color=CommonLocalizedStringColor.GREEN),)
            description_tokens = (CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_TEST_TEXT_WITH_SIM_FIRST_AND_LAST_NAME, tokens=(CommonSimUtils.get_active_sim_info(),), text_color=CommonLocalizedStringColor.BLUE),)
            from sims4communitylib.utils.common_icon_utils import CommonIconUtils
            options = [
                ObjectPickerRow(
                    option_id=1,
                    name=CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_SOME_TEXT_FOR_TESTING),
                    row_description=CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_TEST_BUTTON_ONE),
                    row_tooltip=None,
                    icon=CommonIconUtils.load_checked_square_icon(),
                    tag='Value 1'
                ),
                ObjectPickerRow(
                    option_id=2,
                    name=CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_SOME_TEXT_FOR_TESTING),
                    row_description=CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_TEST_BUTTON_TWO),
                    row_tooltip=None,
                    icon=CommonIconUtils.load_arrow_navigate_into_icon(),
                    tag='Value 2'
                ),
                ObjectPickerRow(
                    option_id=3,
                    name=CommonLocalizationUtils.create_localized_string('Value 3'),
                    row_description=CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_TEST_BUTTON_TWO),
                    row_tooltip=None,
                    icon=CommonIconUtils.load_arrow_navigate_into_icon(),
                    tag='Value 3'
                )
            ]
            dialog = CommonChooseObjectDialog(
                CommonStringId.TESTING_TEST_TEXT_WITH_STRING_TOKEN,
                CommonStringId.TESTING_TEST_TEXT_WITH_STRING_TOKEN,
                tuple(options),
                title_tokens=title_tokens,
                description_tokens=description_tokens,
                per_page=2
            )
            dialog.show(on_chosen=_on_chosen)

    :param title_identifier: The title to display in the dialog.
    :type title_identifier: Union[int, LocalizedString]
    :param description_identifier: The description to display in the dialog.
    :type description_identifier: Union[int, LocalizedString]
    :param choices: The choices that can be chosen.
    :type choices: Iterator[ObjectPickerRow]
    :param title_tokens: Tokens to format into the title.
    :type title_tokens: Iterator[Any], optional
    :param description_tokens: Tokens to format into the description.
    :type description_tokens: Iterator[Any], optional
    :param per_page: The number of rows to display per page. If the number of rows (including rows added after creation) exceeds this value, pagination will be added.
    :type per_page: int
    :param mod_identity: The identity of the mod creating the dialog. See :class:`.CommonModIdentity` for more information.
    :type mod_identity: CommonModIdentity, optional
    """
    def __init__(
        self,
        title_identifier: Union[int, LocalizedString],
        description_identifier: Union[int, LocalizedString],
        choices: Iterator[ObjectPickerRow],
        title_tokens: Iterator[Any]=(),
        description_tokens: Iterator[Any]=(),
        per_page: int=25,
        mod_identity: CommonModIdentity=None
    ):
        super().__init__(
            title_identifier,
            description_identifier,
            choices,
            title_tokens=title_tokens,
            description_tokens=description_tokens,
            mod_identity=mod_identity
        )
        if per_page <= 0:
            raise AssertionError('\'per_page\' must be greater than zero.')
        self._per_page = per_page
        self._always_visible_rows = tuple()
        self._current_page = 1

    @property
    def current_page(self) -> int:
        """Retrieve the current page.

        :return: A number indicating the current page.
        :rtype: int
        """
        return self._current_page

    # noinspection PyMissingOrEmptyDocstring
    @property
    def log_identifier(self) -> str:
        return 's4cl_choose_object_dialog'

    # noinspection PyMissingOrEmptyDocstring
    @property
    def rows(self) -> Tuple[ObjectPickerRow]:
        result: Tuple[ObjectPickerRow] = super().rows
        return result

    @property
    def always_visible_rows(self) -> Tuple[ObjectPickerRow]:
        """A collection of rows that will always appear in the dialog no matter which page.

        .. note:: These rows are added to the dialog before the normal rows are added to the dialog.

        :return: A collection of rows added to the dialog that will always appear.
        :rtype: Tuple[ObjectPickerRow]
        """
        return self._always_visible_rows

    # noinspection PyMissingOrEmptyDocstring
    def add_row(self, choice: ObjectPickerRow, *_, always_visible: bool=False, **__):
        """add_row(row, *_, always_on_visible=False, **__)

        Add a row to the dialog.

        :param choice: The row to add.
        :type choice: ObjectPickerRow
        :param always_visible: If set to True, the row will always appear in the dialog no matter which page. If False, the row will act as normal.
        :type always_visible: bool, optional
        """
        if not always_visible:
            super().add_row(choice, *_, **__)
            return
        try:
            self._always_visible_rows += (choice,)
        except Exception as ex:
            CommonExceptionHandler.log_exception(self.mod_identity, 'add_row', exception=ex)

    def show(
        self,
        on_chosen: Callable[[Any, CommonChoiceOutcome], Any]=CommonFunctionUtils.noop,
        picker_type: UiObjectPicker.UiObjectPickerObjectPickerType=UiObjectPicker.UiObjectPickerObjectPickerType.OBJECT,
        page: int=1,
        sim_info: SimInfo=None,
        categories: Iterator[CommonDialogObjectOptionCategory]=()
    ):
        """show(\
            on_chosen=CommonFunctionUtils.noop,\
            picker_type=UiObjectPicker.UiObjectPickerObjectPickerType.OBJECT,\
            page=1,\
            sim_info=None\
        )

        Show the dialog and invoke the callbacks upon the player making a choice.

        :param on_chosen: A callback invoked upon the player choosing something from the list.
        :type on_chosen: Callable[[Any, CommonChoiceOutcome]
        :param picker_type: The layout of the dialog.
        :type picker_type: UiObjectPicker.UiObjectPickerObjectPickerType
        :param page: The page to display. Ignored if there is only one page of choices.
        :type page: int
        :param sim_info: The Sim that will appear in the dialog image. The default Sim is the Active Sim.
        :type sim_info: SimInfo
        :param categories: A collection of categories do display in the dialog.
        :type categories: Iterator[CommonDialogObjectOptionCategory]
        """
        self._current_page = page
        try:
            return self._show(
                on_chosen=on_chosen,
                picker_type=picker_type,
                page=page,
                sim_info=sim_info,
                categories=categories
            )
        except Exception as ex:
            CommonExceptionHandler.log_exception(self.mod_identity, 'show', exception=ex)

    def _show(
        self,
        on_chosen: Callable[[Any, CommonChoiceOutcome], Any]=CommonFunctionUtils.noop,
        picker_type: UiObjectPicker.UiObjectPickerObjectPickerType=UiObjectPicker.UiObjectPickerObjectPickerType.OBJECT,
        page: int=1,
        sim_info: SimInfo=None,
        categories: Iterator[CommonDialogObjectOptionCategory]=()
    ):
        self.log.format_with_message('Attempting to display choices.', page=page)
        _dialog = self._create_dialog(picker_type=picker_type, categories=categories)
        if _dialog is None:
            self.log.error('_dialog was None for some reason.')
            return

        if on_chosen is None:
            raise ValueError('on_chosen was None.')

        if len(self.always_visible_rows) == 0 and len(self.rows) == 0:
            raise AssertionError('No rows have been provided. Add rows to the dialog before attempting to display it.')

        if page < 0:
            raise AssertionError('page cannot be less than zero.')

        @CommonExceptionHandler.catch_exceptions(self.mod_identity.name)
        def _on_chosen(dialog: UiObjectPicker):
            if not dialog.accepted:
                self.log.debug('Dialog cancelled.')
                return on_chosen(None, CommonChoiceOutcome.CANCEL)
            choice = CommonDialogUtils.get_chosen_item(dialog)
            if choice == 'S4CL_NEXT':
                self.log.debug('Next chosen.')
                self.show(on_chosen=on_chosen, picker_type=picker_type, page=page + 1, sim_info=sim_info, categories=categories)
                return True
            elif choice == 'S4CL_PREVIOUS':
                self.log.debug('Previous chosen.')
                self.show(on_chosen=on_chosen, picker_type=picker_type, page=page - 1, sim_info=sim_info, categories=categories)
                return True
            self.log.format_with_message('Choice made.', choice=choice)
            result = on_chosen(choice, CommonChoiceOutcome.CHOICE_MADE)
            self.log.format_with_message('Finished handling choice.', result=result)
            return result

        number_of_rows = len(self.rows)
        self.log.format(number_of_rows=number_of_rows, per_page=self._per_page)
        if number_of_rows > self._per_page:
            number_of_pages = math.ceil(number_of_rows / self._per_page)

            if page > number_of_pages:
                raise AssertionError('page was out of range. Number of Pages: {}, Requested Page: {}'.format(str(number_of_pages), str(page)))
            # Add the rows that are always visible.
            for always_visible_rows in self.always_visible_rows:
                _dialog.add_row(always_visible_rows)

            # Add the rows that should show on the current page.
            start_index = (page - 1) * self._per_page
            end_index = page * self._per_page
            self.log.format(start_index=start_index, end_index=end_index)
            current_choices = self.rows[start_index:end_index]
            self.log.format(current_rows=current_choices)
            for row in current_choices:
                _dialog.add_row(row)

            tag_list = [(abs(hash(category.object_category)) % (10 ** 8)) for category in categories]

            if page > 1:
                self.log.format_with_message('Adding Previous.', page=page, number_of_pages=number_of_pages)
                previous_choice = ObjectPickerRow(
                    option_id=len(self.rows) + 2,
                    name=CommonLocalizationUtils.create_localized_string(CommonStringId.PREVIOUS),
                    row_description=None,
                    row_tooltip=CommonLocalizationUtils.create_localized_tooltip(CommonStringId.PREVIOUS),
                    icon=CommonIconUtils.load_arrow_left_icon(),
                    tag_list=tag_list,
                    tag='S4CL_PREVIOUS'
                )
                _dialog.add_row(previous_choice)
            else:
                self.log.format_with_message('Not adding Previous.', page=page)
            if page < number_of_pages:
                self.log.format_with_message('Adding Next.', page=page, number_of_pages=number_of_pages)
                next_choice = ObjectPickerRow(
                    option_id=len(self.rows) + 1,
                    name=CommonLocalizationUtils.create_localized_string(CommonStringId.NEXT),
                    row_description=None,
                    row_tooltip=CommonLocalizationUtils.create_localized_tooltip(CommonStringId.NEXT),
                    icon=CommonIconUtils.load_arrow_right_icon(),
                    tag_list=tag_list,
                    tag='S4CL_NEXT'
                )
                _dialog.add_row(next_choice)
            else:
                self.log.format_with_message('Not adding Next.', page=page, number_of_pages=number_of_pages)
        else:
            self.log.debug('Adding all choices')
            for always_visible_rows in self.always_visible_rows:
                _dialog.add_row(always_visible_rows)
            for row in self.rows:
                _dialog.add_row(row)

        _dialog.add_listener(_on_chosen)
        _dialog.show_dialog()

    def _create_dialog(
        self,
        picker_type: UiObjectPicker.UiObjectPickerObjectPickerType=UiObjectPicker.UiObjectPickerObjectPickerType.OBJECT,
        sim_info: SimInfo=None,
        categories: Iterator[CommonDialogObjectOptionCategory]=()
    ) -> Union[UiObjectPicker, None]:
        try:
            from collections import namedtuple
            object_category_type = namedtuple('object_category_type', ('object_category', 'icon', 'category_name'))
            object_categories = list()
            for category in tuple(categories):
                object_categories.append(object_category_type(category.object_category, lambda *_, **__: IconInfoData(icon_resource=CommonIconUtils._load_icon(category.icon)), CommonLocalizationUtils.create_localized_string(category.category_name)))

            if len(object_categories) > 0:
                return CommonUiObjectCategoryPicker.TunableFactory().default(
                    sim_info or CommonSimUtils.get_active_sim_info(),
                    text=lambda *_, **__: self.description,
                    title=lambda *_, **__: self.title,
                    min_selectable=1,
                    max_selectable=1,
                    picker_type=picker_type,
                    use_dropdown_filter=True,
                    object_categories=tuple(object_categories)
                )
            else:
                return UiObjectPicker.TunableFactory().default(
                    sim_info or CommonSimUtils.get_active_sim_info(),
                    text=lambda *_, **__: self.description,
                    title=lambda *_, **__: self.title,
                    min_selectable=1,
                    max_selectable=1,
                    picker_type=picker_type
                )
        except Exception as ex:
            CommonExceptionHandler.log_exception(self.mod_identity, '_create_dialog', exception=ex)
        return None


@sims4.commands.Command('s4clib_testing.show_choose_object_dialog', command_type=sims4.commands.CommandType.Live)
def _common_testing_show_choose_object_dialog(_connection: int=None):
    output = sims4.commands.CheatOutput(_connection)
    output('Showing test choose object dialog.')

    def _on_chosen(choice: str, outcome: CommonChoiceOutcome):
        output('Chose {} with result: {}.'.format(pformat(choice), pformat(outcome)))

    try:
        # LocalizedStrings within other LocalizedStrings
        title_tokens = (CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_SOME_TEXT_FOR_TESTING, text_color=CommonLocalizedStringColor.GREEN),)
        description_tokens = (CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_TEST_TEXT_WITH_SIM_FIRST_AND_LAST_NAME, tokens=(CommonSimUtils.get_active_sim_info(),), text_color=CommonLocalizedStringColor.BLUE),)
        from sims4communitylib.utils.common_icon_utils import CommonIconUtils
        options = [
            ObjectPickerRow(
                option_id=1,
                name=CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_SOME_TEXT_FOR_TESTING),
                row_description=CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_TEST_BUTTON_ONE),
                row_tooltip=None,
                icon=CommonIconUtils.load_checked_square_icon(),
                tag='Value 1'
            ),
            ObjectPickerRow(
                option_id=2,
                name=CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_SOME_TEXT_FOR_TESTING),
                row_description=CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_TEST_BUTTON_TWO),
                row_tooltip=None,
                icon=CommonIconUtils.load_arrow_navigate_into_icon(),
                tag='Value 2'
            ),
            ObjectPickerRow(
                option_id=3,
                name=CommonLocalizationUtils.create_localized_string('Value 3'),
                row_description=CommonLocalizationUtils.create_localized_string(CommonStringId.TESTING_TEST_BUTTON_TWO),
                row_tooltip=None,
                icon=CommonIconUtils.load_arrow_navigate_into_icon(),
                tag='Value 3'
            )
        ]
        dialog = CommonChooseObjectDialog(
            CommonStringId.TESTING_TEST_TEXT_WITH_STRING_TOKEN,
            CommonStringId.TESTING_TEST_TEXT_WITH_STRING_TOKEN,
            tuple(options),
            title_tokens=title_tokens,
            description_tokens=description_tokens,
            per_page=2
        )
        dialog.show(on_chosen=_on_chosen)
    except Exception as ex:
        CommonExceptionHandler.log_exception(ModInfo.get_identity(), 'Failed to show dialog', exception=ex)
        output('Failed to show dialog, please locate your exception log file.')
    output('Done showing.')
