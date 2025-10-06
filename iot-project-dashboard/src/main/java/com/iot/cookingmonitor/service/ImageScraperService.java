package com.iot.cookingmonitor.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;
import java.util.ArrayList;
import java.util.List;

@Service
public class ImageScraperService {

    @Value("${IMAGE_SERVER_URL:http://209.38.30.63:8000}")
    private String baseUrl;

    public String getFirstImageUrl(Integer sessionNumber) {
        try {
            String url = baseUrl + "/" + sessionNumber + "/";
            Document doc = Jsoup.connect(url).get();

            // Look for image links in the HTML
            Elements links = doc.select("a[href]");

            String lastImageUrl = null;
            for (Element link : links) {
                String href = link.attr("href");
                if (isImageFile(href)) {
                    lastImageUrl = url + href;
                }
            }

            // Return the last image found, or null to use fallback
            return lastImageUrl;
        } catch (Exception e) {
            System.err.println("Error scraping images for session " + sessionNumber + ": " + e.getMessage());
            return null;
        }
    }

    public List<String> getAllImageUrls(Integer sessionNumber) {
        List<String> imageUrls = new ArrayList<>();
        try {
            String url = baseUrl + "/" + sessionNumber + "/";
            Document doc = Jsoup.connect(url).get();

            // Look for image links in the HTML
            Elements links = doc.select("a[href]");

            for (Element link : links) {
                String href = link.attr("href");
                if (isImageFile(href)) {
                    imageUrls.add(url + href);
                }
            }
        } catch (Exception e) {
            System.err.println("Error scraping images for session " + sessionNumber + ": " + e.getMessage());
        }
        return imageUrls;
    }

    private boolean isImageFile(String filename) {
        if (filename == null) return false;
        String lower = filename.toLowerCase();
        return lower.endsWith(".jpg") || lower.endsWith(".jpeg") ||
               lower.endsWith(".png") || lower.endsWith(".gif") ||
               lower.endsWith(".webp");
    }
}