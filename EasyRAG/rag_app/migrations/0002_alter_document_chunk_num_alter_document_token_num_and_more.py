# Generated by Django 5.2.3 on 2025-06-13 15:28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rag_app", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="document",
            name="chunk_num",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="document",
            name="token_num",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="knowledgebase",
            name="chunk_num",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="knowledgebase",
            name="document_num",
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name="knowledgebase",
            name="language",
            field=models.CharField(default="Chinese", max_length=50),
        ),
        migrations.AlterField(
            model_name="knowledgebase",
            name="name",
            field=models.CharField(max_length=128),
        ),
        migrations.AlterField(
            model_name="knowledgebase",
            name="vector_similarity_weight",
            field=models.FloatField(default=0.2),
        ),
    ]
