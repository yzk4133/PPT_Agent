"use server";

import { db } from "@/server/db";

export async function addToFavorites(documentId: string) {
  try {
    // Check if already favorited
    const existing = await db.favoriteDocument.findFirst({
      where: {
        documentId,
      },
    });

    if (existing) {
      return { error: "Document is already in favorites" };
    }

    // Add to favorites
    await db.favoriteDocument.create({
      data: {
        documentId,
        userId: "01"
      },
    });

    return { success: true };
  } catch (error) {
    console.error("Error adding to favorites:", error);
    return { error: "Failed to add to favorites" };
  }
}

export async function removeFromFavorites(documentId: string) {
  try {
    await db.favoriteDocument.deleteMany({
      where: {
        documentId,
      },
    });

    return { success: true };
  } catch (error) {
    console.error("Error removing from favorites:", error);
    return { error: "Failed to remove from favorites" };
  }
}
