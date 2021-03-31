# Generated by Django 2.2.16 on 2021-03-23 15:03

from django.db import migrations
import v1.blocks
import wagtail.core.blocks
import wagtail.core.fields


class Migration(migrations.Migration):

    dependencies = [
        ('v1', '0252_filterable_block_order_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='legacyblogpage',
            name='content',
            field=wagtail.core.fields.StreamField([('content', wagtail.core.blocks.RawHTMLBlock(help_text='Content from WordPress unescaped.')), ('feedback', wagtail.core.blocks.StructBlock([('was_it_helpful_text', wagtail.core.blocks.CharBlock(default='Was this page helpful to you?', help_text='Use this field only for feedback forms that use "Was this helpful?" radio buttons.', required=False)), ('intro_text', wagtail.core.blocks.CharBlock(help_text='Optional feedback intro', required=False)), ('question_text', wagtail.core.blocks.CharBlock(help_text='Optional expansion on intro', required=False)), ('radio_intro', wagtail.core.blocks.CharBlock(help_text='Leave blank unless you are building a feedback form with extra radio-button prompts, as in /owning-a-home/help-us-improve/.', required=False)), ('radio_text', wagtail.core.blocks.CharBlock(default='This information helps us understand your question better.', required=False)), ('radio_question_1', wagtail.core.blocks.CharBlock(default='How soon do you expect to buy a home?', required=False)), ('radio_question_2', wagtail.core.blocks.CharBlock(default='Do you currently own a home?', required=False)), ('button_text', wagtail.core.blocks.CharBlock(default='Submit')), ('contact_advisory', wagtail.core.blocks.RichTextBlock(help_text='Use only for feedback forms that ask for a contact email', required=False))])), ('reusable_text', v1.blocks.ReusableTextChooserBlock('v1.ReusableText'))]),
        ),
    ]
