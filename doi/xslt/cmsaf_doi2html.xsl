<?xml version="1.0"?>
<!--
please take care !!!
in this template the registration of the datacite namespace is missing.
the datacite namespace will be set programmatically. please don't add it to this file,
as it will break the routines using this file.
-->
<xsl:stylesheet version="1.0"
                xmlns:default="http://www.w3.org/1999/xhtml"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                exclude-result-prefixes="datacite xsl default"
        >
    <xsl:output
            method="html"
            media-type="text/html"
            doctype-public="-//W3C//DTD HTML 4.01 Transitional//EN"
            indent="no"
            encoding="UTF-8"/>

    <xsl:template match="/datacite:resource">
        <tr>
            <td class="left" colspan="1" rowspan="1">
                <xsl:value-of select="datacite:titles/datacite:title"/><br/>
                <xsl:value-of select="datacite:titles/datacite:title[@titleType='Subtitle']"/>
            </td>
            <td class="left" colspan="1" rowspan="1">
                <xsl:element name="a">
                    <xsl:attribute name="class">ExternalLink</xsl:attribute>
                    <xsl:attribute name="target">_blank</xsl:attribute>
                    <xsl:attribute name="title">External Link http://dx.doi.org/<xsl:value-of select="datacite:identifier[@identifierType='DOI']"/>
                        (Opens new window)
                    </xsl:attribute>
                    <xsl:attribute name="href">http://dx.doi.org/<xsl:value-of select="datacite:identifier[@identifierType='DOI']"/>
                    </xsl:attribute>
                    <xsl:value-of select="datacite:identifier[@identifierType='DOI']"/>
                </xsl:element>
            </td>
            <td class="left" colspan="1" rowspan="1">
                <xsl:element name="a">
                    <xsl:attribute name="class">charme-Dataset</xsl:attribute>
                    <xsl:attribute name="target">_blank</xsl:attribute>
                    <xsl:attribute name="title">CHARMe http://dx.doi.org/<xsl:value-of select="datacite:identifier[@identifierType='DOI']"/>
                        (Opens CHARMe plugin)
                    </xsl:attribute>
                    <xsl:attribute name="href">http://dx.doi.org/<xsl:value-of select="datacite:identifier[@identifierType='DOI']"/>
                    </xsl:attribute>
                </xsl:element>
            </td>
        </tr>
    </xsl:template>
</xsl:stylesheet>
