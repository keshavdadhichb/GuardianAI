/*
  Warnings:

  - Added the required column `verdict` to the `AlertEvent` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "public"."AlertEvent" ADD COLUMN     "verdict" TEXT NOT NULL;
